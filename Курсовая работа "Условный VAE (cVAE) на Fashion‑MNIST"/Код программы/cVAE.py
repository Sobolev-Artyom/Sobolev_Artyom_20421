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
from sklearn.metrics import confusion_matrix, classification_report, f1_score, accuracy_score, silhouette_score, \
    calinski_harabasz_score
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import pandas as pd
import json
import os
from datetime import datetime
import time
import random
import warnings
from scipy import stats

warnings.filterwarnings('ignore')


# =============================================================================
# КОНФИГУРАЦИЯ СРЕДЫ И ВЕРСИИ
# =============================================================================
def print_environment_info():
    """Информация о среде выполнения и версиях"""
    # Определяем устройство с приоритетом на GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    env_info = {
        'timestamp': datetime.now().isoformat(),
        'python_version': '3.8+',
        'torch_version': torch.__version__,
        'torchvision_version': torchvision.__version__,
        'numpy_version': np.__version__,
        'sklearn_version': '1.2+',
        'cuda_available': torch.cuda.is_available(),
        'cuda_version': torch.version.cuda if torch.cuda.is_available() else 'N/A',
        'device': str(device),  # Сохраняем как строку для сериализации
        'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
        'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'
    }
    return env_info, device


# Фиксация случайных seed для воспроизводимости
SEED = 15
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False  


# =============================================================================
# АРХИТЕКТУРА cVAE
# =============================================================================
class ConditionalVAE(nn.Module):
    def __init__(self, image_size=784, hidden_dim=400, latent_dim=64,
                 num_classes=10, label_embedding_dim=32, use_layer_norm=True):
        super(ConditionalVAE, self).__init__()

        self.image_size = image_size
        self.latent_dim = latent_dim
        self.num_classes = num_classes
        self.label_embedding_dim = label_embedding_dim
        self.use_layer_norm = use_layer_norm

        # Embedding для меток
        self.label_embedding = nn.Embedding(num_classes, label_embedding_dim)

        # Энкодер: [x, embedding(y)] → z
        encoder_layers = [
            nn.Linear(image_size + label_embedding_dim, hidden_dim),
            nn.ReLU(),
        ]

        if use_layer_norm:
            encoder_layers.append(nn.LayerNorm(hidden_dim))

        encoder_layers.extend([
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        ])

        if use_layer_norm:
            encoder_layers.append(nn.LayerNorm(hidden_dim))

        self.encoder = nn.Sequential(*encoder_layers)

        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)

        # Декодер: [z, embedding(y)] → x_hat
        decoder_layers = [
            nn.Linear(latent_dim + label_embedding_dim, hidden_dim),
            nn.ReLU(),
        ]

        if use_layer_norm:
            decoder_layers.append(nn.LayerNorm(hidden_dim))

        decoder_layers.extend([
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        ])

        if use_layer_norm:
            decoder_layers.append(nn.LayerNorm(hidden_dim))

        decoder_layers.extend([
            nn.Linear(hidden_dim, image_size),
            nn.Sigmoid()
        ])

        self.decoder = nn.Sequential(*decoder_layers)

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

    def get_latent_representation(self, x, y):
        """Получение латентного представления без reparameterization"""
        with torch.no_grad():
            mu, _ = self.encode(x.view(-1, self.image_size), y)
            return mu

    def forward(self, x, y):
        mu, logvar = self.encode(x.view(-1, self.image_size), y)
        z = self.reparameterize(mu, logvar)
        return self.decode(z, y), mu, logvar


# =============================================================================
# ЛИНЕЙНЫЙ КЛАССИФИКАТОР ДЛЯ LINEAR EVALUATION
# =============================================================================
class LinearClassifier(nn.Module):
    """Простой линейный классификатор для оценки качества эмбеддингов"""

    def __init__(self, input_dim, num_classes):
        super(LinearClassifier, self).__init__()
        self.fc = nn.Linear(input_dim, num_classes)

    def forward(self, x):
        return self.fc(x)


def linear_evaluation(model, train_loader, test_loader, device, experiment_name):
    """Linear evaluation на латентных представлениях возвращает точность на тестовом наборе"""
    print(f"🔍 Starting linear evaluation for {experiment_name}...")

    model.eval()

    # Сбор латентных представлений и меток
    train_features, train_labels = [], []
    test_features, test_labels = [], []

    # Сбор тренировочных данных
    with torch.no_grad():
        for data, labels in train_loader:
            data = data.to(device)
            labels = labels.to(device)

            # Получаем латентные представления
            features = model.get_latent_representation(data, labels)
            train_features.append(features.cpu().numpy())
            train_labels.append(labels.cpu().numpy())

    # Сбор тестовых данных
    with torch.no_grad():
        for data, labels in test_loader:
            data = data.to(device)
            labels = labels.to(device)

            features = model.get_latent_representation(data, labels)
            test_features.append(features.cpu().numpy())
            test_labels.append(labels.cpu().numpy())

    # Объединяем данные
    X_train = np.vstack(train_features)
    y_train = np.concatenate(train_labels)
    X_test = np.vstack(test_features)
    y_test = np.concatenate(test_labels)

    print(f"📊 Linear evaluation data shapes:")
    print(f"   Train: {X_train.shape}, Test: {X_test.shape}")

    # Обучаем линейный классификатор
    linear_model = LogisticRegression(
        random_state=SEED,
        max_iter=1000,
        multi_class='multinomial',
        solver='lbfgs',
        C=1.0
    )

    linear_model.fit(X_train, y_train)

    # Предсказания и метрики
    y_pred = linear_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')

    # Матрица ошибок
    cm = confusion_matrix(y_test, y_pred)

    print(f"📈 Linear Evaluation Results for {experiment_name}:")
    print(f"   ✅ Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print(f"   ✅ F1-score: {f1:.4f} ({f1 * 100:.2f}%)")

    # Визуализация матрицы ошибок
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=range(10), yticklabels=range(10))
    plt.title(f'Confusion Matrix - Linear Evaluation\n{experiment_name}\nAccuracy: {accuracy * 100:.2f}%')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.tight_layout()
    plt.savefig(f'results/confusion_matrix_linear_{experiment_name}.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Проверка достижения целевой точности
    target_accuracy = 0.90  # 90%
    if accuracy >= target_accuracy:
        print(f"🎯 TARGET ACHIEVED! Accuracy ≥ 90%: {accuracy * 100:.2f}%")
    else:
        print(f"📉 Target not reached: {accuracy * 100:.2f}% < 90%")

    return {
        'accuracy': accuracy,
        'accuracy_percent': accuracy * 100,
        'f1_score': f1,
        'f1_score_percent': f1 * 100,
        'target_achieved': accuracy >= target_accuracy,
        'confusion_matrix': cm.tolist()
    }


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
def load_fashion_mnist(batch_size=256): 
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
    """Вычисление метрик качества реконструкции с правильными размерностями"""
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
    # Приводим x к той же форме, что и recon_x [batch_size, 784]
    x_flat = x.view(-1, 784)
    BCE = F.binary_cross_entropy(recon_x, x_flat, reduction='sum')
    KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    ELBO = BCE + beta * KLD
    return ELBO, BCE, KLD


# =============================================================================
# ТАБЛИЦЫ MSE/PSNR ПО КЛАССАМ
# =============================================================================
def calculate_class_wise_metrics(model, test_loader, device, experiment_name):
    """Вычисление MSE и PSNR по классам"""
    model.eval()

    class_mse = {i: [] for i in range(10)}
    class_psnr = {i: [] for i in range(10)}

    with torch.no_grad():
        for data, labels in test_loader:
            data = data.to(device)
            labels = labels.to(device)

            recon_batch, mu, logvar = model(data, labels)

            # Вычисляем метрики для каждого изображения
            for i in range(len(data)):
                original = data[i].view(1, -1)
                reconstructed = recon_batch[i].view(1, -1)

                # MSE
                mse = F.mse_loss(reconstructed, original).item()

                # PSNR
                psnr = 20 * torch.log10(1.0 / torch.sqrt(torch.tensor(mse))).item()

                class_idx = labels[i].item()
                class_mse[class_idx].append(mse)
                class_psnr[class_idx].append(psnr)

    # Вычисляем средние значения по классам
    class_metrics = {}
    for class_idx in range(10):
        if class_mse[class_idx]:  # проверяем, что есть данные
            class_metrics[class_idx] = {
                'mse_mean': np.mean(class_mse[class_idx]),
                'mse_std': np.std(class_mse[class_idx]),
                'psnr_mean': np.mean(class_psnr[class_idx]),
                'psnr_std': np.std(class_psnr[class_idx]),
                'samples': len(class_mse[class_idx])
            }

    # Создаем таблицу
    metrics_df = pd.DataFrame({
        'Class': range(10),
        'MSE_Mean': [class_metrics[i]['mse_mean'] for i in range(10)],
        'MSE_Std': [class_metrics[i]['mse_std'] for i in range(10)],
        'PSNR_Mean': [class_metrics[i]['psnr_mean'] for i in range(10)],
        'PSNR_Std': [class_metrics[i]['psnr_std'] for i in range(10)],
        'Samples': [class_metrics[i]['samples'] for i in range(10)]
    })

    # Сохраняем таблицу
    metrics_df.to_csv(f'results/class_metrics_{experiment_name}.csv', index=False)

    # Визуализация метрик по классам
    plt.figure(figsize=(15, 5))

    plt.subplot(1, 2, 1)
    plt.bar(metrics_df['Class'], metrics_df['MSE_Mean'],
            yerr=metrics_df['MSE_Std'], capsize=5, alpha=0.7, color='skyblue')
    plt.title(f'MSE by Class\n{experiment_name}')
    plt.xlabel('Class')
    plt.ylabel('MSE')
    plt.xticks(range(10))
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.bar(metrics_df['Class'], metrics_df['PSNR_Mean'],
            yerr=metrics_df['PSNR_Std'], capsize=5, alpha=0.7, color='lightcoral')
    plt.title(f'PSNR by Class\n{experiment_name}')
    plt.xlabel('Class')
    plt.ylabel('PSNR (dB)')
    plt.xticks(range(10))
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'results/class_metrics_visualization_{experiment_name}.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Class-wise metrics saved for {experiment_name}")
    return class_metrics, metrics_df


# =============================================================================
# ВИЗУАЛИЗАЦИЯ MU, SIGMA И ЛАТЕНТНОГО ПРОСТРАНСТВА
# =============================================================================
def visualize_latent_distributions(model, data_loader, device, experiment_name):
    """Визуализация распределений mu, sigma и латентного пространства"""
    model.eval()
    mus, logvars, labels_list = [], [], []

    with torch.no_grad():
        for data, labels in data_loader:
            # Перемещаем данные на устройство
            data = data.to(device)
            labels = labels.to(device)

            mu, logvar = model.encode(data.view(-1, 784), labels)
            # Перемещаем обратно на CPU для визуализации
            mus.append(mu.cpu().numpy())
            logvars.append(logvar.cpu().numpy())
            labels_list.append(labels.cpu().numpy())

            # Ограничиваем количество данных для визуализации
            if len(mus) > 10:
                break

    if not mus:
        print("⚠ No data for latent distribution visualization")
        return

    mus = np.vstack(mus)
    logvars = np.vstack(logvars)
    labels_list = np.concatenate(labels_list)
    sigmas = np.exp(0.5 * logvars)  # преобразуем logvar в sigma

    # Выбираем несколько латентных размерностей для визуализации
    n_latent_dims = min(8, mus.shape[1])

    # 1. Визуализация mu по классам
    plt.figure(figsize=(15, 10))

    for i in range(n_latent_dims):
        plt.subplot(3, 4, i + 1)
        for class_idx in range(10):
            class_mask = labels_list == class_idx
            if np.any(class_mask):
                plt.hist(mus[class_mask, i], bins=30, alpha=0.7,
                         label=f'Class {class_idx}', density=True)
        plt.title(f'Mu dim {i}')
        plt.xlabel('Value')
        plt.ylabel('Density')
        if i == 0:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.suptitle(f'Latent Mu Distributions by Class\n{experiment_name}', fontsize=16)
    plt.tight_layout()
    plt.savefig(f'results/mu_distributions_{experiment_name}.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Визуализация sigma по классам
    plt.figure(figsize=(15, 10))

    for i in range(n_latent_dims):
        plt.subplot(3, 4, i + 1)
        for class_idx in range(10):
            class_mask = labels_list == class_idx
            if np.any(class_mask):
                plt.hist(sigmas[class_mask, i], bins=30, alpha=0.7,
                         label=f'Class {class_idx}', density=True)
        plt.title(f'Sigma dim {i}')
        plt.xlabel('Value')
        plt.ylabel('Density')
        if i == 0:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.suptitle(f'Latent Sigma Distributions by Class\n{experiment_name}', fontsize=16)
    plt.tight_layout()
    plt.savefig(f'results/sigma_distributions_{experiment_name}.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 3. Scatter plot первых двух латентных размерностей
    plt.figure(figsize=(12, 10))

    scatter = plt.scatter(mus[:, 0], mus[:, 1], c=labels_list,
                          cmap='tab10', alpha=0.6, s=20)
    plt.colorbar(scatter, label='Class')
    plt.title(f'Latent Space Scatter (First 2 Dimensions)\n{experiment_name}')
    plt.xlabel('Mu dimension 0')
    plt.ylabel('Mu dimension 1')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'results/latent_scatter_{experiment_name}.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 4. Улучшенная t-SNE визуализация
    try:
        # Используем больше данных для t-SNE
        mus_tsne, logvars_tsne, labels_tsne = [], [], []
        with torch.no_grad():
            for data, labels in data_loader:
                data = data.to(device)
                labels = labels.to(device)

                mu, logvar = model.encode(data.view(-1, 784), labels)
                mus_tsne.append(mu.cpu().numpy())
                logvars_tsne.append(logvar.cpu().numpy())
                labels_tsne.append(labels.cpu().numpy())

                if len(mus_tsne) > 20:  # больше данных для лучшей t-SNE
                    break

        mus_tsne = np.vstack(mus_tsne)
        labels_tsne = np.concatenate(labels_tsne)

        # t-SNE для mu
        tsne = TSNE(n_components=2, random_state=SEED, perplexity=30, n_iter=1000)
        mus_2d = tsne.fit_transform(mus_tsne)

        plt.figure(figsize=(12, 10))
        scatter = plt.scatter(mus_2d[:, 0], mus_2d[:, 1], c=labels_tsne,
                              cmap='tab10', alpha=0.7, s=30)
        plt.colorbar(scatter, label='Class')
        plt.title(f'Latent Space t-SNE Visualization\n{experiment_name}')
        plt.xlabel('t-SNE 1')
        plt.ylabel('t-SNE 2')

        # Добавляем аннотации для центроидов классов
        for class_idx in range(10):
            class_mask = labels_tsne == class_idx
            if np.any(class_mask):
                centroid = np.mean(mus_2d[class_mask], axis=0)
                plt.annotate(f'C{class_idx}', centroid,
                             xytext=(5, 5), textcoords='offset points',
                             fontweight='bold', fontsize=8,
                             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'results/latent_tsne_detailed_{experiment_name}.png', dpi=150, bbox_inches='tight')
        plt.close()

    except Exception as e:
        print(f"❌ Error in detailed t-SNE visualization: {e}")

    print(f"✅ Latent distributions visualization saved for {experiment_name}")


# =============================================================================
# АНАЛИЗ СТРУКТУРЫ ЛАТЕНТНОГО ПРОСТРАНСТВА
# =============================================================================
def convert_to_serializable(obj):
    """Рекурсивно преобразует объект в сериализуемый формат"""
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, torch.device):
        return str(obj)  # Преобразуем device в строку
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_serializable(item) for item in obj)
    elif hasattr(obj, '__dict__'):
        # Для объектов с атрибутами
        return convert_to_serializable(obj.__dict__)
    else:
        return obj


def analyze_latent_structure(model, data_loader, device, experiment_name):
    """Анализ структуры латентного пространства с комментариями"""
    model.eval()
    mus, labels_list = [], []

    with torch.no_grad():
        for data, labels in data_loader:
            data = data.to(device)
            labels = labels.to(device)

            mu, _ = model.encode(data.view(-1, 784), labels)
            mus.append(mu.cpu().numpy())
            labels_list.append(labels.cpu().numpy())

            if len(mus) > 15:  # достаточно данных для анализа
                break

    if not mus:
        return "⚠ No data for latent structure analysis"

    mus = np.vstack(mus)
    labels_list = np.concatenate(labels_list)

    # Анализ кластеризации
    analysis_results = {
        'experiment_name': experiment_name,
        'n_samples': len(mus),
        'latent_dim': mus.shape[1],
        'n_classes': len(np.unique(labels_list))
    }

    # Вычисляем метрики кластеризации
    try:
        silhouette = silhouette_score(mus, labels_list)
        calinski_harabasz = calinski_harabasz_score(mus, labels_list)

        analysis_results['silhouette_score'] = float(silhouette)
        analysis_results['calinski_harabasz_score'] = float(calinski_harabasz)
    except Exception as e:
        print(f"⚠ Clustering metrics calculation failed: {e}")
        analysis_results['silhouette_score'] = -1
        analysis_results['calinski_harabasz_score'] = -1

    # Анализ разделимости классов
    class_separability = {}
    for i in range(10):
        for j in range(i + 1, 10):
            mask_i = labels_list == i
            mask_j = labels_list == j

            if np.sum(mask_i) > 0 and np.sum(mask_j) > 0:
                # Простое измерение расстояния между центрами классов
                centroid_i = np.mean(mus[mask_i], axis=0)
                centroid_j = np.mean(mus[mask_j], axis=0)
                distance = np.linalg.norm(centroid_i - centroid_j)
                class_separability[f'{i}-{j}'] = float(distance)

    analysis_results['class_separability'] = class_separability

    # Генерация комментариев
    comments = generate_latent_structure_comments(analysis_results, mus, labels_list)
    analysis_results['comments'] = comments

    # Преобразуем все в сериализуемый формат
    analysis_results = convert_to_serializable(analysis_results)

    # Сохраняем анализ
    with open(f'results/latent_analysis_{experiment_name}.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)

    return analysis_results


def generate_latent_structure_comments(analysis, mus, labels):
    """Генерация комментариев о структуре латентного пространства"""
    comments = []

    # Анализ на основе silhouette score
    silhouette = analysis.get('silhouette_score', -1)
    if silhouette > 0.5:
        comments.append("✅ Отличная кластеризация: классы хорошо разделены в латентном пространстве")
    elif silhouette > 0.25:
        comments.append("⚠ Умеренная кластеризация: некоторые классы пересекаются")
    elif silhouette >= 0:
        comments.append("❌ Слабая кластеризация: классы сильно перемешаны")
    else:
        comments.append("📊 Метрика кластеризации недоступна")

    # Анализ распределения расстояний между классами
    separability = analysis.get('class_separability', {})
    if separability:
        distances = list(separability.values())
        avg_distance = np.mean(distances)
        std_distance = np.std(distances)

        comments.append(f"📏 Среднее расстояние между классами: {avg_distance:.3f} (±{std_distance:.3f})")

        if std_distance > avg_distance * 0.5:
            comments.append("🔍 Заметна разная степень разделимости между парами классов")
        else:
            comments.append("📊 Разделимость классов относительно равномерная")

    # Анализ выбросов
    z_scores = np.abs(stats.zscore(mus, axis=0))
    outlier_mask = (z_scores > 3).any(axis=1)
    outlier_count = np.sum(outlier_mask)
    outlier_percentage = (outlier_count / len(mus)) * 100

    comments.append(f"🎯 Выбросы (>3σ): {int(outlier_count)} точек ({outlier_percentage:.1f}%)")

    if outlier_percentage > 5:
        comments.append("⚠ Заметное количество выбросов в латентном пространстве")
    else:
        comments.append("✅ Выбросы в пределах нормы")

    # Анализ компактности классов
    class_compactness = {}
    for class_idx in range(10):
        class_mask = labels == class_idx
        if np.sum(class_mask) > 1:
            class_data = mus[class_mask]
            variance = np.mean(np.var(class_data, axis=0))
            class_compactness[class_idx] = float(variance)

    if class_compactness:
        avg_compactness = np.mean(list(class_compactness.values()))
        compactness_std = np.std(list(class_compactness.values()))

        comments.append(f"📦 Средняя компактность классов: {avg_compactness:.3f} (±{compactness_std:.3f})")

        if compactness_std > avg_compactness * 0.5:
            comments.append("🔍 Классы имеют разную степень компактности")

    return comments

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

        # Оптимизатор
        self.optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, patience=config.get('patience', 5), factor=0.5
        )

        # Сбор логов
        self.log_data = {
            'train_losses': [], 'val_losses': [], 'train_elbo': [], 'val_elbo': [],
            'train_bce': [], 'train_kld': [], 'val_bce': [], 'val_kld': [],
            'learning_rates': [], 'epoch_times': [], 'best_val_loss': float('inf'),
            'test_metrics': {}, 'linear_evaluation': {}, 'start_time': None, 'end_time': None
        }

    def train_epoch(self, epoch):
        self.model.train()
        total_loss, total_bce, total_kld = 0, 0, 0

        for batch_idx, (data, labels) in enumerate(self.train_loader):
            # Перемещаем данные на устройство (GPU)
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

            # Логирование прогресса для больших батчей
            if batch_idx % 50 == 0:
                print(f'    Batch {batch_idx}/{len(self.train_loader)}, Loss: {loss.item() / len(data):.4f}')

        n_samples = len(self.train_loader.dataset)
        return (total_loss / n_samples, total_bce / n_samples, total_kld / n_samples)

    def validate_epoch(self):
        self.model.eval()
        total_loss, total_bce, total_kld = 0, 0, 0

        with torch.no_grad():
            for data, labels in self.val_loader:
                # Перемещаем данные на устройство (GPU)
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
        if torch.cuda.is_available():
            print(f"🎯 Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠ Using CPU - training will be slower")

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
                  f'LR: {current_lr:.2e}, BCE: {val_bce:8.2f}, KLD: {val_kld:8.2f}, Time: {epoch_time:5.1f}s')

        total_time = time.time() - start_time
        self.log_data['end_time'] = datetime.now().isoformat()
        self.log_data['total_training_time'] = float(total_time)

        # Финальное тестирование
        self.evaluate_test_set()

        # Linear evaluation
        self.perform_linear_evaluation()

        print(f"✅ Training completed in {total_time:.1f}s")
        print(f"🏆 Best val ELBO: {self.log_data['best_val_loss']:.2f}")

        return self.log_data

    def evaluate_test_set(self):
        """Оценка на тестовом наборе с расширенными метриками"""
        self.model.eval()
        total_loss, total_bce, total_kld = 0, 0, 0
        all_mse, all_psnr = [], []

        with torch.no_grad():
            for data, labels in self.test_loader:
                data = data.to(self.device)
                labels = labels.to(self.device)

                recon_batch, mu, logvar = self.model(data, labels)
                loss, bce, kld = compute_elbo(recon_batch, data, mu, logvar, self.config['beta'])

                total_loss += loss.item()
                total_bce += bce.item()
                total_kld += kld.item()

                # Вычисляем MSE и PSNR для батча
                for i in range(len(data)):
                    original = data[i].view(1, -1)
                    reconstructed = recon_batch[i].view(1, -1)

                    mse = F.mse_loss(reconstructed, original).item()
                    psnr = 20 * torch.log10(1.0 / torch.sqrt(torch.tensor(mse))).item()

                    all_mse.append(mse)
                    all_psnr.append(psnr)

        # Вычисление метрик
        metrics = {
            'elbo': total_loss / len(self.test_loader.dataset),
            'bce': total_bce / len(self.test_loader.dataset),
            'kld': total_kld / len(self.test_loader.dataset),
            'mse_mean': np.mean(all_mse),
            'mse_std': np.std(all_mse),
            'psnr_mean': np.mean(all_psnr),
            'psnr_std': np.std(all_psnr)
        }

        self.log_data['test_metrics'] = metrics

        # Дополнительно: метрики по классам
        class_metrics, metrics_df = calculate_class_wise_metrics(
            self.model, self.test_loader, self.device, self.config['experiment_name']
        )
        self.log_data['class_wise_metrics'] = class_metrics
        self.log_data['metrics_dataframe'] = metrics_df.to_dict()

        return metrics

    def perform_linear_evaluation(self):
        """Выполнение linear evaluation на эмбеддингах"""
        linear_results = linear_evaluation(
            self.model, self.train_loader, self.test_loader,
            self.device, self.config['experiment_name']
        )
        self.log_data['linear_evaluation'] = linear_results
        return linear_results

    def perform_comprehensive_analysis(self):
        """Выполнение комплексного анализа после обучения"""
        print(f"🔍 Performing comprehensive analysis for {self.config['experiment_name']}...")

        # Визуализация распределений
        visualize_latent_distributions(
            self.model, self.test_loader, self.device, self.config['experiment_name']
        )

        # Анализ структуры
        latent_analysis = analyze_latent_structure(
            self.model, self.test_loader, self.device, self.config['experiment_name']
        )

        # Вывод комментариев
        if 'comments' in latent_analysis:
            print(f"\n📊 Latent Structure Analysis for {self.config['experiment_name']}:")
            for comment in latent_analysis['comments']:
                print(f"   {comment}")

        self.log_data['latent_analysis'] = latent_analysis
        return latent_analysis


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

            if len(latents) > 5:
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

    # Преобразуем config и log_data в сериализуемый формат
    serializable_config = convert_to_serializable(config)
    serializable_log_data = convert_to_serializable(log_data)
    serializable_env_info = convert_to_serializable(env_info)

    log_entry = {
        'experiment_name': experiment_name,
        'environment_info': serializable_env_info,
        'config': serializable_config,
        'training_logs': serializable_log_data,
        'timestamp': datetime.now().isoformat()
    }

    log_filename = f"logs/{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)

    print(f"📁 Logs saved to: {log_filename}")
    return log_filename


def run_experiment(config, env_info):
    """Запуск одного эксперимента с расширенным анализом"""
    print(f"\n{'=' * 60}")
    print(f"🔬 Experiment: {config['experiment_name']}")
    print(f"📊 Label embedding dim: {config['label_embedding_dim']}")
    print(f"🎯 Latent dim: {config['latent_dim']}")
    print(f"💻 Device: {config['device']}")
    print(f"📐 Normalization: {config.get('normalization', 'LayerNorm')}")
    print(f"{'=' * 60}")

    try:
        # Загрузка данных
        train_loader, val_loader, test_loader = load_fashion_mnist(config['batch_size'])

        # Создание модели в зависимости от типа нормализации
        normalization_type = config.get('normalization', 'LayerNorm')

        if normalization_type == 'LayerNorm':
            model = ConditionalVAE(
                latent_dim=config['latent_dim'],
                label_embedding_dim=config['label_embedding_dim'],
                hidden_dim=config['hidden_dim'],
                use_layer_norm=True
            ).to(config['device'])
        elif normalization_type == 'NoNorm':
            model = ConditionalVAE(
                latent_dim=config['latent_dim'],
                label_embedding_dim=config['label_embedding_dim'],
                hidden_dim=config['hidden_dim'],
                use_layer_norm=False
            ).to(config['device'])
        else:
            raise ValueError(f"Unknown normalization type: {normalization_type}")

        print(f"🔧 Model parameters: {sum(p.numel() for p in model.parameters()):,}")
        if torch.cuda.is_available():
            print(f"🎯 Model moved to GPU: {next(model.parameters()).is_cuda}")
        print(f"📐 Using {normalization_type}")

        # Обучение
        trainer = cVAETrainer(model, train_loader, val_loader, test_loader, config)
        log_data = trainer.train()

        # Расширенные визуализации и анализ
        visualize_training_progress(log_data, config['experiment_name'])
        visualize_latent_space(model, val_loader, config['device'], config['experiment_name'])
        generate_10x10_panel(model, config['device'], config['experiment_name'])
        generate_class_comparison_panel(model, test_loader, config['device'], config['experiment_name'])

        # Новые функции анализа
        trainer.perform_comprehensive_analysis()

        # Сохранение логов
        log_file = save_experiment_logs(config['experiment_name'], log_data, config, env_info)

        # Возвращаем результат с правильной структурой
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

    # Группируем эксперименты по типу нормализации
    ln_exps = {k: v for k, v in successful_exps.items() if v['config'].get('normalization') == 'LayerNorm'}
    bn_exps = {k: v for k, v in successful_exps.items() if v['config'].get('normalization') == 'BatchNorm'}
    none_exps = {k: v for k, v in successful_exps.items() if v['config'].get('normalization') == 'NoNorm'}

    # Создаем большую фигуру для всех графиков
    fig = plt.figure(figsize=(25, 20))

    # Определяем сетку для subplots
    gs = fig.add_gridspec(4, 4)

    # 1. Сравнение val_ELBO по эпохам
    ax1 = fig.add_subplot(gs[0, 0])
    # 2. Сравнение val_BCE по эпохам
    ax2 = fig.add_subplot(gs[0, 1])
    # 3. Сравнение val_KLD по эпохам
    ax3 = fig.add_subplot(gs[0, 2])
    # 4. Сравнение PSNR по экспериментам
    ax4 = fig.add_subplot(gs[0, 3])

    # 5. Сравнение финальных метрик (bar plot)
    ax5 = fig.add_subplot(gs[1, 0])
    # 6. Сравнение времени обучения
    ax6 = fig.add_subplot(gs[1, 1])
    # 7. Сравнение точности линейной оценки
    ax7 = fig.add_subplot(gs[1, 2])
    # 8. Сравнение лучших val_ELBO
    ax8 = fig.add_subplot(gs[1, 3])

    # 9. Heatmap сравнения метрик между экспериментами
    ax9 = fig.add_subplot(gs[2, :2])
    # 10. Scatter plot: PSNR vs Accuracy
    ax10 = fig.add_subplot(gs[2, 2:])

    # 11. Сравнение скорости сходимости (первые 20 эпох)
    ax11 = fig.add_subplot(gs[3, :])

    colors_ln = plt.cm.Blues(np.linspace(0.4, 0.9, len(ln_exps)))
    colors_bn = plt.cm.Reds(np.linspace(0.4, 0.9, len(bn_exps)))
    colors_none = plt.cm.Greens(np.linspace(0.4, 0.9, len(none_exps)))

    # Подготовка данных для всех графиков
    all_exp_data = []
    exp_names = []
    norm_types = []
    colors_list = []

    # LayerNorm experiments
    for i, (exp_name, result) in enumerate(ln_exps.items()):
        log_data = result['log_data']
        config = result['config']
        label = f"LN-emb{config['label_embedding_dim']}"

        # Данные для графиков по эпохам
        epochs = range(1, len(log_data['val_losses']) + 1)

        # val_ELBO
        ax1.plot(epochs, log_data['val_losses'], label=label, color=colors_ln[i], linewidth=2)
        # val_BCE
        ax2.plot(epochs, log_data['val_bce'], label=label, color=colors_ln[i], linewidth=2)
        # val_KLD
        ax3.plot(epochs, log_data['val_kld'], label=label, color=colors_ln[i], linewidth=2)

        # Скорость сходимости (первые 20 эпох)
        max_epochs_plot = min(20, len(log_data['val_losses']))
        ax11.plot(range(1, max_epochs_plot + 1), log_data['val_losses'][:max_epochs_plot],
                  label=label, color=colors_ln[i], linewidth=2)

        # Сохраняем данные для агрегированных графиков
        exp_data = {
            'name': exp_name,
            'label': label,
            'norm_type': 'LayerNorm',
            'color': colors_ln[i],
            'final_val_elbo': log_data['val_losses'][-1],
            'final_val_bce': log_data['val_bce'][-1],
            'final_val_kld': log_data['val_kld'][-1],
            'best_val_elbo': log_data['best_val_loss'],
            'test_psnr': log_data['test_metrics']['psnr_mean'],
            'test_mse': log_data['test_metrics']['mse_mean'],
            'test_elbo': log_data['test_metrics']['elbo'],
            'training_time': log_data['total_training_time'],
            'linear_accuracy': log_data['linear_evaluation'].get('accuracy_percent', 0),
            'embedding_dim': config['label_embedding_dim']
        }
        all_exp_data.append(exp_data)
        exp_names.append(label)
        norm_types.append('LayerNorm')
        colors_list.append(colors_ln[i])

    # BatchNorm experiments
    for i, (exp_name, result) in enumerate(bn_exps.items()):
        log_data = result['log_data']
        config = result['config']
        label = f"BN-emb{config['label_embedding_dim']}"

        epochs = range(1, len(log_data['val_losses']) + 1)

        # val_ELBO
        ax1.plot(epochs, log_data['val_losses'], label=label, color=colors_bn[i], linewidth=2, linestyle='--')
        # val_BCE
        ax2.plot(epochs, log_data['val_bce'], label=label, color=colors_bn[i], linewidth=2, linestyle='--')
        # val_KLD
        ax3.plot(epochs, log_data['val_kld'], label=label, color=colors_bn[i], linewidth=2, linestyle='--')

        # Скорость сходимости
        max_epochs_plot = min(20, len(log_data['val_losses']))
        ax11.plot(range(1, max_epochs_plot + 1), log_data['val_losses'][:max_epochs_plot],
                  label=label, color=colors_bn[i], linewidth=2, linestyle='--')

        exp_data = {
            'name': exp_name,
            'label': label,
            'norm_type': 'BatchNorm',
            'color': colors_bn[i],
            'final_val_elbo': log_data['val_losses'][-1],
            'final_val_bce': log_data['val_bce'][-1],
            'final_val_kld': log_data['val_kld'][-1],
            'best_val_elbo': log_data['best_val_loss'],
            'test_psnr': log_data['test_metrics']['psnr_mean'],
            'test_mse': log_data['test_metrics']['mse_mean'],
            'test_elbo': log_data['test_metrics']['elbo'],
            'training_time': log_data['total_training_time'],
            'linear_accuracy': log_data['linear_evaluation'].get('accuracy_percent', 0),
            'embedding_dim': config['label_embedding_dim']
        }
        all_exp_data.append(exp_data)
        exp_names.append(label)
        norm_types.append('BatchNorm')
        colors_list.append(colors_bn[i])

    # NoNorm experiments
    for i, (exp_name, result) in enumerate(none_exps.items()):
        log_data = result['log_data']
        config = result['config']
        label = f"NoNorm-emb{config['label_embedding_dim']}"

        epochs = range(1, len(log_data['val_losses']) + 1)

        # val_ELBO
        ax1.plot(epochs, log_data['val_losses'], label=label, color=colors_none[i], linewidth=2, linestyle=':')
        # val_BCE
        ax2.plot(epochs, log_data['val_bce'], label=label, color=colors_none[i], linewidth=2, linestyle=':')
        # val_KLD
        ax3.plot(epochs, log_data['val_kld'], label=label, color=colors_none[i], linewidth=2, linestyle=':')

        # Скорость сходимости
        max_epochs_plot = min(20, len(log_data['val_losses']))
        ax11.plot(range(1, max_epochs_plot + 1), log_data['val_losses'][:max_epochs_plot],
                  label=label, color=colors_none[i], linewidth=2, linestyle=':')

        exp_data = {
            'name': exp_name,
            'label': label,
            'norm_type': 'NoNorm',
            'color': colors_none[i],
            'final_val_elbo': log_data['val_losses'][-1],
            'final_val_bce': log_data['val_bce'][-1],
            'final_val_kld': log_data['val_kld'][-1],
            'best_val_elbo': log_data['best_val_loss'],
            'test_psnr': log_data['test_metrics']['psnr_mean'],
            'test_mse': log_data['test_metrics']['mse_mean'],
            'test_elbo': log_data['test_metrics']['elbo'],
            'training_time': log_data['total_training_time'],
            'linear_accuracy': log_data['linear_evaluation'].get('accuracy_percent', 0),
            'embedding_dim': config['label_embedding_dim']
        }
        all_exp_data.append(exp_data)
        exp_names.append(label)
        norm_types.append('NoNorm')
        colors_list.append(colors_none[i])

    # Настройка графиков по эпохам
    for ax, title, ylabel in [(ax1, 'Validation ELBO', 'ELBO'),
                              (ax2, 'Validation BCE', 'BCE'),
                              (ax3, 'Validation KLD', 'KLD')]:
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('Epoch')
        ax.set_ylabel(ylabel)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

    # 4. Сравнение PSNR по экспериментам
    psnr_values = [exp['test_psnr'] for exp in all_exp_data]
    ax4.bar(range(len(psnr_values)), psnr_values, color=colors_list, alpha=0.7)
    ax4.set_title('Test PSNR Comparison', fontsize=12, fontweight='bold')
    ax4.set_ylabel('PSNR (dB)')
    ax4.set_xticks(range(len(exp_names)))
    ax4.set_xticklabels(exp_names, rotation=45, ha='right')
    ax4.grid(True, alpha=0.3)

    # Добавляем значения на bars
    for i, v in enumerate(psnr_values):
        ax4.text(i, v + 0.1, f'{v:.1f}', ha='center', va='bottom', fontsize=8)

    # 5. Сравнение финальных метрик (val_ELBO, val_BCE, val_KLD)
    x_pos = np.arange(len(all_exp_data))
    width = 0.25

    final_elbo = [exp['final_val_elbo'] for exp in all_exp_data]
    final_bce = [exp['final_val_bce'] for exp in all_exp_data]
    final_kld = [exp['final_val_kld'] for exp in all_exp_data]

    ax5.bar(x_pos - width, final_elbo, width, label='Final Val ELBO', alpha=0.7)
    ax5.bar(x_pos, final_bce, width, label='Final Val BCE', alpha=0.7)
    ax5.bar(x_pos + width, final_kld, width, label='Final Val KLD', alpha=0.7)

    ax5.set_title('Final Validation Metrics', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Loss Value')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(exp_names, rotation=45, ha='right')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # 6. Сравнение времени обучения
    training_times = [exp['training_time'] for exp in all_exp_data]
    ax6.bar(range(len(training_times)), training_times, color=colors_list, alpha=0.7)
    ax6.set_title('Training Time Comparison', fontsize=12, fontweight='bold')
    ax6.set_ylabel('Time (seconds)')
    ax6.set_xticks(range(len(exp_names)))
    ax6.set_xticklabels(exp_names, rotation=45, ha='right')
    ax6.grid(True, alpha=0.3)

    for i, v in enumerate(training_times):
        ax6.text(i, v + 5, f'{v:.0f}s', ha='center', va='bottom', fontsize=8)

    # 7. Сравнение точности линейной оценки
    accuracies = [exp['linear_accuracy'] for exp in all_exp_data]
    bars = ax7.bar(range(len(accuracies)), accuracies, color=colors_list, alpha=0.7)
    ax7.set_title('Linear Evaluation Accuracy', fontsize=12, fontweight='bold')
    ax7.set_ylabel('Accuracy (%)')
    ax7.set_xticks(range(len(exp_names)))
    ax7.set_xticklabels(exp_names, rotation=45, ha='right')
    ax7.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='90% Target')
    ax7.legend()
    ax7.grid(True, alpha=0.3)

    # Подсвечиваем достигшие 90%
    for i, (bar, acc) in enumerate(zip(bars, accuracies)):
        if acc >= 90:
            bar.set_color('green')
            bar.set_alpha(0.9)
        ax7.text(i, acc + 1, f'{acc:.1f}%', ha='center', va='bottom', fontsize=8)

    # 8. Сравнение лучших val_ELBO
    best_elbos = [exp['best_val_elbo'] for exp in all_exp_data]
    ax8.bar(range(len(best_elbos)), best_elbos, color=colors_list, alpha=0.7)
    ax8.set_title('Best Validation ELBO', fontsize=12, fontweight='bold')
    ax8.set_ylabel('ELBO')
    ax8.set_xticks(range(len(exp_names)))
    ax8.set_xticklabels(exp_names, rotation=45, ha='right')
    ax8.grid(True, alpha=0.3)

    for i, v in enumerate(best_elbos):
        ax8.text(i, v + 0.5, f'{v:.1f}', ha='center', va='bottom', fontsize=8)

    # 9. Heatmap сравнения метрик между экспериментами
    metrics_for_heatmap = ['final_val_elbo', 'final_val_bce', 'final_val_kld',
                           'test_psnr', 'test_mse', 'linear_accuracy', 'training_time']
    metric_labels = ['Val ELBO', 'Val BCE', 'Val KLD', 'PSNR', 'Test MSE', 'Accuracy', 'Time(s)']

    heatmap_data = []
    for exp in all_exp_data:
        row = [exp['final_val_elbo'], exp['final_val_bce'], exp['final_val_kld'],
               exp['test_psnr'], exp['test_mse'], exp['linear_accuracy'], exp['training_time']]
        heatmap_data.append(row)

    heatmap_data = np.array(heatmap_data)

    # Нормализуем данные для heatmap (кроме accuracy и PSNR, которые должны быть максимизированы)
    normalized_data = heatmap_data.copy()
    for i, metric in enumerate(metrics_for_heatmap):
        if metric in ['test_psnr', 'linear_accuracy']:
            # Для метрик, которые нужно максимизировать
            normalized_data[:, i] = (heatmap_data[:, i] - heatmap_data[:, i].min()) / (
                        heatmap_data[:, i].max() - heatmap_data[:, i].min())
        else:
            # Для метрик, которые нужно минимизировать (инвертируем)
            normalized_data[:, i] = 1 - (heatmap_data[:, i] - heatmap_data[:, i].min()) / (
                        heatmap_data[:, i].max() - heatmap_data[:, i].min())

    im = ax9.imshow(normalized_data, cmap='RdYlBu', aspect='auto')
    ax9.set_xticks(range(len(metric_labels)))
    ax9.set_xticklabels(metric_labels, rotation=45, ha='right')
    ax9.set_yticks(range(len(exp_names)))
    ax9.set_yticklabels(exp_names)
    ax9.set_title('Normalized Metrics Heatmap\n(Darker = Better)', fontsize=12, fontweight='bold')

    # Добавляем значения в heatmap
    for i in range(len(exp_names)):
        for j in range(len(metric_labels)):
            text = ax9.text(j, i, f'{heatmap_data[i, j]:.1f}',
                            ha="center", va="center", color="black", fontsize=7)

    plt.colorbar(im, ax=ax9)

    # 10. Scatter plot: PSNR vs Accuracy
    for i, exp in enumerate(all_exp_data):
        ax10.scatter(exp['test_psnr'], exp['linear_accuracy'],
                     color=exp['color'], s=100, alpha=0.7, label=exp['label'])
        ax10.annotate(exp['label'], (exp['test_psnr'], exp['linear_accuracy']),
                      xytext=(5, 5), textcoords='offset points', fontsize=8)

    ax10.set_xlabel('PSNR (dB)')
    ax10.set_ylabel('Linear Accuracy (%)')
    ax10.set_title('PSNR vs Linear Accuracy', fontsize=12, fontweight='bold')
    ax10.axhline(y=90, color='red', linestyle='--', alpha=0.5, label='90% Accuracy')
    ax10.grid(True, alpha=0.3)
    ax10.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    # 11. Сравнение скорости сходимости (первые 20 эпох)
    ax11.set_title('Early Training Convergence (First 20 Epochs)', fontsize=12, fontweight='bold')
    ax11.set_xlabel('Epoch')
    ax11.set_ylabel('Validation ELBO')
    ax11.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax11.grid(True, alpha=0.3)

    plt.suptitle('Comprehensive Comparison of cVAE Experiments with Different Normalization Techniques',
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('results/comprehensive_experiments_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ Comprehensive experiments comparison visualization saved")

    # Дополнительно: сохраняем сводную таблицу
    summary_df = pd.DataFrame(all_exp_data)
    summary_df.to_csv('results/experiments_summary_table.csv', index=False)
    print("✅ Experiments summary table saved")


# =============================================================================
# ОСНОВНАЯ ПРОГРАММА
# =============================================================================
def main():
    """Основная функция программы"""

    # Информация о среде с определением устройства
    env_info, device = print_environment_info()

    print("🎮 Conditional VAE on Fashion-MNIST with Linear Evaluation")
    print("🎯 Target: Linear evaluation accuracy ≥ 90%")
    print("📊 Environment Info:")
    for key, value in env_info.items():
        print(f"   {key}: {value}")

    # Дополнительная информация о GPU
    if torch.cuda.is_available():
        print(f"🎯 Using GPU: {torch.cuda.get_device_name(0)}")
        print(f"🎯 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f} GB")
    else:
        print("⚠ Using CPU - training will be slower")

    print("=" * 60)

    # Создание директорий
    os.makedirs('results', exist_ok=True)
    os.makedirs('results/models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    # Конфигурации экспериментов с разными типами нормализации
    configs = [
        # Layer Normalization experiments
        {
            'experiment_name': 'cvae_emb64',
            'latent_dim': 32,
            'label_embedding_dim': 64,
            'hidden_dim': 400,
            'learning_rate': 3e-4,
            'beta': 0.3,
            'epochs': 75,
            'batch_size': 128,
            'patience': 5,
            'device': str(device),
            'normalization': 'LayerNorm'
        },
        {
            'experiment_name': 'cvae_emb128',
            'latent_dim': 32,
            'label_embedding_dim': 128,
            'hidden_dim': 400,
            'learning_rate': 3e-4,
            'beta': 0.3,
            'epochs': 75,
            'batch_size': 128,
            'patience': 5,
            'device': str(device),
            'normalization': 'LayerNorm'
        },
        {
            'experiment_name': 'cvae_emb256',
            'latent_dim': 32,
            'label_embedding_dim': 256,
            'hidden_dim': 400,
            'learning_rate': 3e-4,
            'beta': 0.3,
            'epochs': 75,
            'batch_size': 128,
            'patience': 5,
            'device': str(device),
            'normalization': 'LayerNorm'
        }
    ]

    all_results = {}
    target_achievers = []

    # Запуск экспериментов
    for config in configs:
        # Восстанавливаем device из строки для использования в обучении
        config_with_device = config.copy()
        config_with_device['device'] = device

        result = run_experiment(config_with_device, env_info)
        all_results[config['experiment_name']] = result

        if result['success']:
            test_metrics = result['log_data']['test_metrics']
            linear_eval = result['log_data'].get('linear_evaluation', {})
            accuracy_percent = linear_eval.get('accuracy_percent', 0)

            print(f"✅ {config['experiment_name']} - "
                  f"Test ELBO: {test_metrics['elbo']:.2f}, "
                  f"Linear Accuracy: {accuracy_percent:.2f}%")

            # Проверка на точность
            if accuracy_percent >= 90:
                target_achievers.append(config['experiment_name'])
                print(f"🎯 TARGET ACHIEVED! {config['experiment_name']} reached {accuracy_percent:.2f}%")
        else:
            print(f"❌ {config['experiment_name']} failed")

    # Сравнительная визуализация
    create_comparison_visualization(all_results)

    # Сводный отчет
    save_summary_report(all_results, env_info, target_achievers)

    print("\n🎉 All experiments completed!")
    print("📁 Check 'results/' directory for visualizations")
    print("📁 Check 'logs/' directory for detailed logs")


def save_summary_report(all_results, env_info, target_achievers):
    """Сохранение сводного отчета"""
    successful_exps = {}
    for exp_name, result in all_results.items():
        if result.get('success') and 'config' in result:
            successful_exps[exp_name] = result

    summary = {
        'environment_info': convert_to_serializable(env_info),
        'timestamp': datetime.now().isoformat(),
        'total_experiments': len(all_results),
        'successful_experiments': len(successful_exps),
        'target_achievers': target_achievers,
        'target_achievers_count': len(target_achievers),
        'experiments_summary': {}
    }

    for exp_name, result in successful_exps.items():
        log_data = result['log_data']
        config = result['config']
        linear_eval = log_data.get('linear_evaluation', {})

        summary['experiments_summary'][exp_name] = {
            'label_embedding_dim': config['label_embedding_dim'],
            'latent_dim': config['latent_dim'],
            'best_val_elbo': float(log_data['best_val_loss']),
            'total_training_time': float(log_data['total_training_time']),
            'test_metrics': convert_to_serializable(log_data['test_metrics']),
            'linear_evaluation': convert_to_serializable(linear_eval),
            'final_train_elbo': float(log_data['train_losses'][-1]) if log_data['train_losses'] else 0,
            'final_val_elbo': float(log_data['val_losses'][-1]) if log_data['val_losses'] else 0,
            'target_achieved': exp_name in target_achievers,
            'log_file': result.get('log_file', 'N/A')
        }

    # Преобразуем summary в сериализуемый формат
    summary = convert_to_serializable(summary)

    # Сейв отчета
    with open('logs/experiments_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Статистика в компактном формате
    print("\n📊 FINAL SUMMARY:")
    print("=" * 60)
    print(f"🎯 Target achievers ({len(target_achievers)}/{len(successful_exps)}): {target_achievers}")

    for exp_name, exp_summary in summary['experiments_summary'].items():
        linear_acc = exp_summary['linear_evaluation'].get('accuracy_percent', 0)
        target_status = "✅ ACHIEVED" if exp_summary['target_achieved'] else "❌ Not achieved"

        print(f"\n🔬 {exp_name}:")
        print(f"   Embedding dim: {exp_summary['label_embedding_dim']}")
        print(f"   Linear Accuracy: {linear_acc:.2f}% - {target_status}")
        print(f"   Best Val ELBO: {exp_summary['best_val_elbo']:.2f}")
        print(f"   Test ELBO: {exp_summary['test_metrics']['elbo']:.2f}")
        print(f"   Test BCE: {exp_summary['test_metrics']['bce']:.2f}")
        print(f"   Test KLD: {exp_summary['test_metrics']['kld']:.2f}")
        print(f"   Training Time: {exp_summary['total_training_time']:.1f}s")


if __name__ == "__main__":
    # Импорт для версий
    import torchvision

    main()
