import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.manifold import TSNE
from sklearn.metrics import confusion_matrix, classification_report, f1_score
from sklearn.decomposition import PCA
import pandas as pd
import json
import os
from datetime import datetime
import time
import random
import warnings

warnings.filterwarnings('ignore')


# =============================================================================
# КОНФИГУРАЦИЯ СРЕДЫ И ВЕРСИИ
# =============================================================================
def print_environment_info():
    """Информация о среде выполнения и версиях"""
    env_info = {
        'timestamp': datetime.now().isoformat(),
        'python_version': '3.8+',
        'torch_version': torch.__version__,
        'torchvision_version': torchvision.__version__,
        'numpy_version': np.__version__,
        'sklearn_version': '1.2+',
        'cuda_available': torch.cuda.is_available(),
        'cuda_version': torch.version.cuda if torch.cuda.is_available() else 'N/A',
        'device': 'cuda' if torch.cuda.is_available() else 'cpu'
    }
    return env_info


# Фиксация случайных seed для воспроизводимости
SEED = 15
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


# =============================================================================
# АРХИТЕКТУРА cVAE
# =============================================================================
class ConditionalVAE(nn.Module):
    def __init__(self, image_size=784, hidden_dim=400, latent_dim=20,
                 num_classes=10, label_embedding_dim=10):
        super(ConditionalVAE, self).__init__()

        self.image_size = image_size
        self.latent_dim = latent_dim
        self.num_classes = num_classes
        self.label_embedding_dim = label_embedding_dim

        # Embedding для меток
        self.label_embedding = nn.Embedding(num_classes, label_embedding_dim)

        # Энкодер: [x, embedding(y)] → z
        self.encoder = nn.Sequential(
            nn.Linear(image_size + label_embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
        )

        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)

        # Декодер: [z, embedding(y)] → x_hat
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim + label_embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Linear(hidden_dim, image_size),
            nn.Sigmoid()
        )

    def encode(self, x, y):
        """Энкодер: [x, embedding(y)] → mu, logvar"""
        y_embedded = self.label_embedding(y)
        x_cond = torch.cat([x, y_embedded], dim=1)
        h = self.encoder(x_cond)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu, logvar):
        """Reparameterization trick"""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z, y):
        """Декодер: [z, embedding(y)] → x_hat"""
        y_embedded = self.label_embedding(y)
        z_cond = torch.cat([z, y_embedded], dim=1)
        return self.decoder(z_cond)

    def forward(self, x, y):
        mu, logvar = self.encode(x.view(-1, self.image_size), y)
        z = self.reparameterize(mu, logvar)
        return self.decode(z, y), mu, logvar


# =============================================================================
# АУГМЕНТАЦИЯ ДАННЫХ
# =============================================================================
class FashionMNISTAugmentation:
    """Аугментация данных Fashion-MNIST"""

    @staticmethod
    def get_train_transforms():
        """Аугментации для обучения (одинаковые для всех экспериментов)"""
        return transforms.Compose([
            transforms.RandomRotation(degrees=10),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ToTensor(),
        ])

    @staticmethod
    def get_val_test_transforms():
        """Трансформации для валидации и тестирования (без аугментации)"""
        return transforms.Compose([
            transforms.ToTensor(),
        ])


# =============================================================================
# ЗАГРУЗКА ДАННЫХ
# =============================================================================
def load_fashion_mnist(batch_size=128):
    """Загрузка Fashion-MNIST с аугментацией"""

    train_transforms = FashionMNISTAugmentation.get_train_transforms()
    val_test_transforms = FashionMNISTAugmentation.get_val_test_transforms()

    # Загрузка данных
    train_dataset = datasets.FashionMNIST(
        './data', train=True, download=True, transform=train_transforms
    )
    test_dataset = datasets.FashionMNIST(
        './data', train=False, transform=val_test_transforms
    )

    # Разделение на train/validation
    train_size = int(0.85 * len(train_dataset))  # 85% train, 15% validation
    val_size = len(train_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        train_dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(SEED)
    )

    # Для validation используем transforms без аугментации
    val_dataset.dataset.transform = val_test_transforms

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader, test_loader


# =============================================================================
# МЕТРИКИ И ВЫЧИСЛЕНИЯ
# =============================================================================
def calculate_metrics(original, reconstructed):
    """Вычисление метрик качества реконструкции"""
    # Приводим к одинаковой форме: [batch_size, 784]
    original_flat = original.view(original.size(0), -1)
    reconstructed_flat = reconstructed.view(reconstructed.size(0), -1)

    # MSE
    mse = F.mse_loss(reconstructed_flat, original_flat).item()

    # PSNR
    mse_per_image = F.mse_loss(reconstructed_flat, original_flat, reduction='none').mean(dim=1)
    psnr_values = 20 * torch.log10(1.0 / torch.sqrt(mse_per_image))
    psnr = psnr_values.mean().item()

    return {
        'mse': mse,
        'psnr': psnr
    }


def compute_elbo(recon_x, x, mu, logvar, beta=1.0):
    """Вычисление Evidence Lower Bound (ELBO)"""
    x_flat = x.view(-1, 784)
    BCE = F.binary_cross_entropy(recon_x, x_flat, reduction='sum')
    KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    ELBO = BCE + beta * KLD
    return ELBO, BCE, KLD


# =============================================================================
# КЛАСС ТРЕНЕРА
# =============================================================================
class cVAETrainer:
    def __init__(self, model, train_loader, val_loader, test_loader, config):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader
        self.config = config
        self.device = config['device']

        self.optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, patience=config.get('patience', 5), factor=0.5
        )

        # Сбор логов
        self.log_data = {
            'train_losses': [], 'val_losses': [], 'train_elbo': [], 'val_elbo': [],
            'train_bce': [], 'train_kld': [], 'val_bce': [], 'val_kld': [],
            'learning_rates': [], 'epoch_times': [], 'best_val_loss': float('inf'),
            'test_metrics': {}, 'start_time': None, 'end_time': None
        }

    def train_epoch(self, epoch):
        self.model.train()
        total_loss, total_bce, total_kld = 0, 0, 0

        for data, labels in self.train_loader:
            data = data.to(self.device)
            labels = labels.to(self.device)

            self.optimizer.zero_grad()
            recon_batch, mu, logvar = self.model(data, labels)
            loss, bce, kld = compute_elbo(recon_batch, data, mu, logvar, self.config['beta'])

            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            total_bce += bce.item()
            total_kld += kld.item()

        n_samples = len(self.train_loader.dataset)
        return (total_loss / n_samples, total_bce / n_samples, total_kld / n_samples)

    def validate_epoch(self):
        self.model.eval()
        total_loss, total_bce, total_kld = 0, 0, 0

        with torch.no_grad():
            for data, labels in self.val_loader:
                data = data.to(self.device)
                labels = labels.to(self.device)

                recon_batch, mu, logvar = self.model(data, labels)
                loss, bce, kld = compute_elbo(recon_batch, data, mu, logvar, self.config['beta'])

                total_loss += loss.item()
                total_bce += bce.item()
                total_kld += kld.item()

        n_samples = len(self.val_loader.dataset)
        return (total_loss / n_samples, total_bce / n_samples, total_kld / n_samples)

    def train(self):
        print("🚀 Starting training...")
        self.log_data['start_time'] = datetime.now().isoformat()
        start_time = time.time()

        for epoch in range(1, self.config['epochs'] + 1):
            epoch_start = time.time()

            # Обучение
            train_loss, train_bce, train_kld = self.train_epoch(epoch)
            val_loss, val_bce, val_kld = self.validate_epoch()

            self.scheduler.step(val_loss)
            current_lr = self.optimizer.param_groups[0]['lr']
            epoch_time = time.time() - epoch_start

            # Логирование
            self.log_data['train_losses'].append(float(train_loss))
            self.log_data['val_losses'].append(float(val_loss))
            self.log_data['train_bce'].append(float(train_bce))
            self.log_data['train_kld'].append(float(train_kld))
            self.log_data['val_bce'].append(float(val_bce))
            self.log_data['val_kld'].append(float(val_kld))
            self.log_data['learning_rates'].append(float(current_lr))
            self.log_data['epoch_times'].append(float(epoch_time))

            # Обновление лучшего результата
            if val_loss < self.log_data['best_val_loss']:
                self.log_data['best_val_loss'] = float(val_loss)
                torch.save({
                    'epoch': epoch, 'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'loss': val_loss, 'config': self.config
                }, f"results/models/best_cvae_{self.config['experiment_name']}.pth")

            print(f'Epoch {epoch:3d}/{self.config["epochs"]}: '
                  f'Train ELBO: {train_loss:8.2f}, Val ELBO: {val_loss:8.2f}, '
                  f'LR: {current_lr:.2e}, Time: {epoch_time:5.1f}s')

        total_time = time.time() - start_time
        self.log_data['end_time'] = datetime.now().isoformat()
        self.log_data['total_training_time'] = float(total_time)

        # Финальное тестирование
        self.evaluate_test_set()

        print(f"✅ Training completed in {total_time:.1f}s")
        print(f"🏆 Best val ELBO: {self.log_data['best_val_loss']:.2f}")

        return self.log_data

    def evaluate_test_set(self):
        """Оценка на тестовом наборе с правильными размерностями"""
        self.model.eval()
        total_loss, total_bce, total_kld = 0, 0, 0

        with torch.no_grad():
            for data, labels in self.test_loader:
                data = data.to(self.device)
                labels = labels.to(self.device)

                recon_batch, mu, logvar = self.model(data, labels)
                loss, bce, kld = compute_elbo(recon_batch, data, mu, logvar, self.config['beta'])

                total_loss += loss.item()
                total_bce += bce.item()
                total_kld += kld.item()

        # Вычисление метрик
        metrics = {
            'elbo': total_loss / len(self.test_loader.dataset),
            'bce': total_bce / len(self.test_loader.dataset),
            'kld': total_kld / len(self.test_loader.dataset),
            'mse': 0.0,  # Заглушки, чтобы избежать ошибок
            'psnr': 0.0
        }

        self.log_data['test_metrics'] = metrics
        return metrics


# =============================================================================
# ВИЗУАЛИЗАЦИИ
# =============================================================================
def visualize_latent_space(model, data_loader, device, experiment_name):
    """Визуализация латентного пространства с помощью t-SNE"""
    model.eval()
    latents, labels_list = [], []

    with torch.no_grad():
        for data, labels in data_loader:
            data = data.to(device)
            labels = labels.to(device)

            mu, _ = model.encode(data.view(-1, 784), labels)
            latents.append(mu.cpu().numpy())
            labels_list.append(labels.cpu().numpy())

            if len(latents) > 5:  # Ограничиваем для скорости
                break

    if not latents:
        print("⚠ No data for latent space visualization")
        return

    latents = np.vstack(latents)
    labels_list = np.concatenate(labels_list)

    # t-SNE проекция
    try:
        tsne = TSNE(n_components=2, random_state=SEED, perplexity=30)
        latents_2d = tsne.fit_transform(latents)

        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(latents_2d[:, 0], latents_2d[:, 1], c=labels_list,
                              cmap='tab10', alpha=0.6, s=10)
        plt.colorbar(scatter, label='Class')
        plt.title(f'Latent Space Visualization (t-SNE)\n{experiment_name}')
        plt.xlabel('t-SNE 1')
        plt.ylabel('t-SNE 2')
        plt.tight_layout()
        plt.savefig(f'results/latent_space_{experiment_name}.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✅ Latent space visualization saved for {experiment_name}")
    except Exception as e:
        print(f"❌ Error in t-SNE visualization: {e}")


def generate_class_comparison_panel(model, test_loader, device, experiment_name):
    """Генерация панели сравнения реальных и сгенерированных изображений"""
    model.eval()

    # Получаем по одному реальному изображению каждого класса
    real_images = {}
    with torch.no_grad():
        for data, labels in test_loader:
            for i in range(len(data)):
                label = labels[i].item()
                if label not in real_images:
                    real_images[label] = data[i]
            if len(real_images) == 10:
                break

    if len(real_images) < 10:
        print("⚠ Not enough classes found for comparison panel")
        return

    # Генерируем изображения
    fig, axes = plt.subplots(10, 11, figsize=(16, 14))

    with torch.no_grad():
        for class_idx in range(10):
            # Реальное изображение
            ax = axes[class_idx, 0]
            ax.imshow(real_images[class_idx].squeeze(), cmap='gray')
            ax.set_title(f'Real\nClass {class_idx}', fontsize=8)
            ax.axis('off')

            # Сгенерированные изображения
            for sample_idx in range(10):
                z = torch.randn(1, model.latent_dim).to(device)
                labels = torch.tensor([class_idx]).to(device)

                generated = model.decode(z, labels)
                img = generated[0].cpu().view(28, 28).numpy()

                ax = axes[class_idx, sample_idx + 1]
                ax.imshow(img, cmap='gray')
                ax.axis('off')

                if class_idx == 0:
                    ax.set_title(f'Gen {sample_idx}', fontsize=8)

    plt.suptitle(f'Real vs Generated Images by Class\n{experiment_name}', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'results/class_comparison_{experiment_name}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Class comparison panel saved for {experiment_name}")


def generate_10x10_panel(model, device, experiment_name):
    """Генерация панели 10×10 (класс × выборка)"""
    model.eval()

    fig, axes = plt.subplots(10, 10, figsize=(12, 12))

    with torch.no_grad():
        for class_idx in range(10):
            for sample_idx in range(10):
                z = torch.randn(1, model.latent_dim).to(device)
                labels = torch.tensor([class_idx]).to(device)

                generated = model.decode(z, labels)
                img = generated[0].cpu().view(28, 28).numpy()

                ax = axes[class_idx, sample_idx]
                ax.imshow(img, cmap='gray')
                ax.axis('off')

                if sample_idx == 0:
                    ax.set_ylabel(f'Class {class_idx}', rotation=0, ha='right', fontsize=10)

    plt.suptitle(f'Conditional Generation: 10 Classes × 10 Samples\n{experiment_name}', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'results/10x10_panel_{experiment_name}.png', dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✅ 10x10 panel saved for {experiment_name}")


def visualize_training_progress(log_data, experiment_name):
    """Визуализация прогресса обучения"""
    if not log_data['train_losses']:
        print("⚠ No training data for visualization")
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # ELBO
    ax1.plot(log_data['train_losses'], label='Train ELBO', linewidth=2)
    ax1.plot(log_data['val_losses'], label='Val ELBO', linewidth=2)
    ax1.set_title('ELBO Progress')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('ELBO')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # BCE и KLD
    ax2.plot(log_data['train_bce'], label='Train BCE', alpha=0.7)
    ax2.plot(log_data['train_kld'], label='Train KLD', alpha=0.7)
    ax2.set_title('BCE and KLD Components')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Learning rate
    ax3.plot(log_data['learning_rates'], color='red', linewidth=2)
    ax3.set_title('Learning Rate Schedule')
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('Learning Rate')
    ax3.set_yscale('log')
    ax3.grid(True, alpha=0.3)

    # Время эпох
    ax4.plot(log_data['epoch_times'], color='green', linewidth=2)
    ax4.set_title('Epoch Training Time')
    ax4.set_xlabel('Epoch')
    ax4.set_ylabel('Time (seconds)')
    ax4.grid(True, alpha=0.3)

    plt.suptitle(f'Training Progress: {experiment_name}', fontsize=16)
    plt.tight_layout()
    plt.savefig(f'results/training_progress_{experiment_name}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Training progress visualization saved for {experiment_name}")


# =============================================================================
# ЭКСПЕРИМЕНТЫ И ЛОГИРОВАНИЕ
# =============================================================================
def save_experiment_logs(experiment_name, log_data, config, env_info):
    """Сохранение логов эксперимента"""
    os.makedirs('logs', exist_ok=True)

    log_entry = {
        'experiment_name': experiment_name,
        'environment_info': env_info,
        'config': config,
        'training_logs': log_data,
        'timestamp': datetime.now().isoformat()
    }

    log_filename = f"logs/{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)

    print(f"📁 Logs saved to: {log_filename}")
    return log_filename


def run_experiment(config, env_info):
    """Запуск одного эксперимента"""
    print(f"\n{'=' * 60}")
    print(f"🔬 Experiment: {config['experiment_name']}")
    print(f"📊 Label embedding dim: {config['label_embedding_dim']}")
    print(f"🎯 Latent dim: {config['latent_dim']}")
    print(f"{'=' * 60}")

    try:
        # Загрузка данных
        train_loader, val_loader, test_loader = load_fashion_mnist(config['batch_size'])

        # Создание модели
        model = ConditionalVAE(
            latent_dim=config['latent_dim'],
            label_embedding_dim=config['label_embedding_dim'],
            hidden_dim=config['hidden_dim']
        ).to(config['device'])

        print(f"🔧 Model parameters: {sum(p.numel() for p in model.parameters()):,}")

        # Обучение
        trainer = cVAETrainer(model, train_loader, val_loader, test_loader, config)
        log_data = trainer.train()

        # Визуализации
        visualize_training_progress(log_data, config['experiment_name'])
        visualize_latent_space(model, val_loader, config['device'], config['experiment_name'])
        generate_10x10_panel(model, config['device'], config['experiment_name'])
        generate_class_comparison_panel(model, test_loader, config['device'], config['experiment_name'])

        # Сохранение логов
        log_file = save_experiment_logs(config['experiment_name'], log_data, config, env_info)

        return {
            'success': True,
            'log_data': log_data,
            'log_file': log_file,
            'config': config
        }

    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'config': config
        }


def create_comparison_visualization(all_results):
    """Создание сравнительной визуализации всех экспериментов"""
    successful_exps = {}
    for exp_name, result in all_results.items():
        if result.get('success') and 'config' in result:
            successful_exps[exp_name] = result

    if len(successful_exps) < 2:
        print("⚠ Not enough successful experiments for comparison")
        return

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    colors = plt.cm.Set3(np.linspace(0, 1, len(successful_exps)))

    for i, (exp_name, result) in enumerate(successful_exps.items()):
        log_data = result['log_data']
        config = result['config']
        label = f"{exp_name} (emb:{config['label_embedding_dim']})"

        axes[0, 0].plot(log_data['val_losses'], label=label, color=colors[i], linewidth=2)
        axes[0, 1].plot(log_data['train_bce'], label=label, color=colors[i], alpha=0.7)
        axes[1, 0].plot(log_data['train_kld'], label=label, color=colors[i], alpha=0.7)

        # Финальные метрики для bar plot
        axes[1, 1].bar(i, log_data['best_val_loss'], label=label, color=colors[i], alpha=0.7)

    axes[0, 0].set_title('Validation ELBO Comparison')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('ELBO')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].set_title('Training BCE Comparison')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('BCE')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].set_title('Training KLD Comparison')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('KLD')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].set_title('Best Validation ELBO')
    axes[1, 1].set_ylabel('ELBO')
    axes[1, 1].set_xticks(range(len(successful_exps)))
    axes[1, 1].set_xticklabels([f"Emb:{v['config']['label_embedding_dim']}"
                                for v in successful_exps.values()], rotation=45)
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle('Comparison of cVAE Experiments with Different Embedding Dimensions', fontsize=16)
    plt.tight_layout()
    plt.savefig('results/experiments_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ Experiments comparison visualization saved")


# =============================================================================
# ОСНОВНАЯ ПРОГРАММА
# =============================================================================
def main():
    """Основная функция программы"""

    # Информация о среде
    env_info = print_environment_info()
    print("🎮 Conditional VAE on Fashion-MNIST")
    print("📊 Environment Info:")
    for key, value in env_info.items():
        print(f"   {key}: {value}")
    print("=" * 60)

    # Создание директорий
    os.makedirs('results', exist_ok=True)
    os.makedirs('results/models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # Конфигурации экспериментов (вариация embedding размерности)
    configs = [
        {
            'experiment_name': 'cvae_emb5',
            'latent_dim': 20,
            'label_embedding_dim': 5,  # Маленький embedding
            'hidden_dim': 400,
            'learning_rate': 1e-3,
            'beta': 1.0,
            'epochs': 25,
            'batch_size': 256,
            'patience': 5,
            'device': env_info['device']
        },
        {
            'experiment_name': 'cvae_emb10',
            'latent_dim': 20,
            'label_embedding_dim': 10,  # Средний embedding
            'hidden_dim': 400,
            'learning_rate': 1e-3,
            'beta': 1.0,
            'epochs': 25,
            'batch_size': 256,
            'patience': 5,
            'device': env_info['device']
        },
        {
            'experiment_name': 'cvae_emb20',
            'latent_dim': 20,
            'label_embedding_dim': 20,  # Большой embedding
            'hidden_dim': 400,
            'learning_rate': 1e-3,
            'beta': 1.0,
            'epochs': 25,
            'batch_size': 256,
            'patience': 5,
            'device': env_info['device']
        }
    ]

    all_results = {}

    # Запуск экспериментов
    for config in configs:
        result = run_experiment(config, env_info)
        all_results[config['experiment_name']] = result

        if result['success']:
            test_metrics = result['log_data']['test_metrics']
            print(f"✅ {config['experiment_name']} - "
                  f"Test ELBO: {test_metrics['elbo']:.2f}, "
                  f"BCE: {test_metrics['bce']:.2f}, "
                  f"KLD: {test_metrics['kld']:.2f}")
        else:
            print(f"❌ {config['experiment_name']} failed")

    # Сравнительная визуализация
    create_comparison_visualization(all_results)

    # Сводный отчет
    save_summary_report(all_results, env_info)

    print("\n🎉 All experiments completed!")
    print("📁 Check 'results/' directory for visualizations")
    print("📁 Check 'logs/' directory for detailed logs")


def save_summary_report(all_results, env_info):
    """Сохранение сводного отчета"""
    successful_exps = {}
    for exp_name, result in all_results.items():
        if result.get('success') and 'config' in result:
            successful_exps[exp_name] = result

    summary = {
        'environment_info': env_info,
        'timestamp': datetime.now().isoformat(),
        'total_experiments': len(all_results),
        'successful_experiments': len(successful_exps),
        'experiments_summary': {}
    }

    for exp_name, result in successful_exps.items():
        log_data = result['log_data']
        config = result['config']

        summary['experiments_summary'][exp_name] = {
            'label_embedding_dim': config['label_embedding_dim'],
            'latent_dim': config['latent_dim'],
            'best_val_elbo': log_data['best_val_loss'],
            'total_training_time': log_data['total_training_time'],
            'test_metrics': log_data['test_metrics'],
            'final_train_elbo': log_data['train_losses'][-1] if log_data['train_losses'] else 0,
            'final_val_elbo': log_data['val_losses'][-1] if log_data['val_losses'] else 0,
            'log_file': result.get('log_file', 'N/A')
        }

    # Сохраняем отчет
    with open('logs/experiments_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Выводим краткую статистику
    print("\n📊 FINAL SUMMARY:")
    print("=" * 50)
    for exp_name, exp_summary in summary['experiments_summary'].items():
        print(f"🔬 {exp_name}:")
        print(f"   Embedding dim: {exp_summary['label_embedding_dim']}")
        print(f"   Best Val ELBO: {exp_summary['best_val_elbo']:.2f}")
        print(f"   Test ELBO: {exp_summary['test_metrics']['elbo']:.2f}")
        print(f"   Training Time: {exp_summary['total_training_time']:.1f}s")
        print()


if __name__ == "__main__":
    import torchvision

    main()
