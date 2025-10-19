import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import itertools

# Конфигурация
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
batch_size = 128
latent_dim = 20
label_embedding_dim = 10
learning_rate = 1e-3
epochs = 30

# Преобразования данных
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# Загрузка данных
train_dataset = datasets.FashionMNIST('./data', train=True, download=True, transform=transform)
test_dataset = datasets.FashionMNIST('./data', train=False, download=True, transform=transform)

# Сбалансированные загрузчики данных
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# Классы Fashion-MNIST
class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
               'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']

# Модель условного VAE
class ConditionalVAE(nn.Module):
    def __init__(self, img_size=28, latent_dim=20, label_embedding_dim=10, num_classes=10):
        super(ConditionalVAE, self).__init__()
        
        self.img_size = img_size
        self.latent_dim = latent_dim
        self.label_embedding_dim = label_embedding_dim
        self.num_classes = num_classes
        
        # Энкодер
        self.encoder = nn.Sequential(
            nn.Linear(img_size*img_size + label_embedding_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
        )
        
        self.fc_mu = nn.Linear(256, latent_dim)
        self.fc_logvar = nn.Linear(256, latent_dim)
        
        # Декодер
        self.decoder_input = nn.Linear(latent_dim + label_embedding_dim, 256)
        
        self.decoder = nn.Sequential(
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, img_size*img_size),
            nn.Tanh()
        )
        
        # Embedding для меток
        self.label_embedding = nn.Embedding(num_classes, label_embedding_dim)
        
    def encode(self, x, labels):
        # Встраивание меток
        label_emb = self.label_embedding(labels)
        # Конкатенация изображения и embedded метки
        x_cond = torch.cat([x.view(-1, self.img_size*self.img_size), label_emb], dim=1)
        h = self.encoder(x_cond)
        return self.fc_mu(h), self.fc_logvar(h)
    
    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def decode(self, z, labels):
        # Встраивание меток
        label_emb = self.label_embedding(labels)
        # Конкатенация latent vector и embedded метки
        z_cond = torch.cat([z, label_emb], dim=1)
        h = self.decoder_input(z_cond)
        x_recon = self.decoder(h)
        return x_recon.view(-1, 1, self.img_size, self.img_size)
    
    def forward(self, x, labels):
        mu, logvar = self.encode(x, labels)
        z = self.reparameterize(mu, logvar)
        x_recon = self.decode(z, labels)
        return x_recon, mu, logvar

# Функция потерь
def vae_loss(recon_x, x, mu, logvar, beta=1.0):
    # Reconstruction loss (MSE)
    recon_loss = F.mse_loss(recon_x, x, reduction='sum')
    
    # KL divergence
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    
    return recon_loss + beta * kl_loss, recon_loss, kl_loss

# Инициализация модели
model = ConditionalVAE(latent_dim=latent_dim, label_embedding_dim=label_embedding_dim).to(device)
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# Обучение
def train(model, dataloader, optimizer, epoch):
    model.train()
    train_loss = 0
    recon_loss_total = 0
    kl_loss_total = 0
    
    pbar = tqdm(dataloader, desc=f'Epoch {epoch+1}')
    for batch_idx, (data, labels) in enumerate(pbar):
        data = data.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        recon_batch, mu, logvar = model(data, labels)
        loss, recon_loss, kl_loss = vae_loss(recon_batch, data, mu, logvar)
        
        loss.backward()
        train_loss += loss.item()
        recon_loss_total += recon_loss.item()
        kl_loss_total += kl_loss.item()
        
        optimizer.step()
        
        if batch_idx % 100 == 0:
            pbar.set_postfix({
                'Loss': f'{loss.item()/len(data):.4f}',
                'Recon': f'{recon_loss.item()/len(data):.4f}',
                'KL': f'{kl_loss.item()/len(data):.4f}'
            })
    
    return train_loss / len(dataloader.dataset), recon_loss_total / len(dataloader.dataset), kl_loss_total / len(dataloader.dataset)

# Валидация
def validate(model, dataloader):
    model.eval()
    val_loss = 0
    recon_loss_total = 0
    kl_loss_total = 0
    
    with torch.no_grad():
        for data, labels in dataloader:
            data = data.to(device)
            labels = labels.to(device)
            
            recon_batch, mu, logvar = model(data, labels)
            loss, recon_loss, kl_loss = vae_loss(recon_batch, data, mu, logvar)
            
            val_loss += loss.item()
            recon_loss_total += recon_loss.item()
            kl_loss_total += kl_loss.item()
    
    return val_loss / len(dataloader.dataset), recon_loss_total / len(dataloader.dataset), kl_loss_total / len(dataloader.dataset)

# Функция для получения реальных примеров из датасета
def get_real_examples(dataset, num_samples_per_class=10):
    """Возвращает реальные примеры для каждого класса"""
    real_examples = {i: [] for i in range(10)}
    
    for image, label in dataset:
        if len(real_examples[label]) < num_samples_per_class:
            real_examples[label].append(image)
        # Проверяем, собрали ли достаточно примеров для всех классов
        if all(len(examples) == num_samples_per_class for examples in real_examples.values()):
            break
    
    return real_examples

# Усовершенствованная условная генерация с сравнением
def generate_conditionally_with_comparison(model, dataset, num_samples=10):
    model.eval()
    
    # Получаем реальные примеры из датасета
    real_examples = get_real_examples(dataset, num_samples)
    
    # Создаем большую фигуру для сравнения
    fig, axes = plt.subplots(20, num_samples, figsize=(num_samples, 20))
    
    with torch.no_grad():
        for label in range(10):
            # ГЕНЕРИРОВАННЫЕ ИЗОБРАЖЕНИЯ (верхние 10 строк)
            # Создаем latent vectors и метки
            z = torch.randn(num_samples, latent_dim).to(device)
            labels_tensor = torch.tensor([label] * num_samples).to(device)
            
            # Генерируем изображения
            generated = model.decode(z, labels_tensor)
            generated = generated.cpu().numpy()
            
            for j in range(num_samples):
                # Верхняя половина - сгенерированные
                ax_gen = axes[label, j]
                ax_gen.imshow(generated[j, 0], cmap='gray', vmin=-1, vmax=1)
                ax_gen.axis('off')
                
                # Подписи для первого столбца
                if j == 0:
                    ax_gen.set_ylabel(f'Generated\n{class_names[label]}', 
                                    rotation=0, ha='right', va='center', fontsize=8)
            
            # РЕАЛЬНЫЕ ИЗОБРАЖЕНИЯ (нижние 10 строк)
            real_images = real_examples[label]
            
            for j in range(num_samples):
                # Нижняя половина - реальные
                ax_real = axes[label + 10, j]
                real_img = real_images[j].squeeze().numpy()
                ax_real.imshow(real_img, cmap='gray', vmin=-1, vmax=1)
                ax_real.axis('off')
                
                # Подписи для первого столбца
                if j == 0:
                    ax_real.set_ylabel(f'Real\n{class_names[label]}', 
                                     rotation=0, ha='right', va='center', fontsize=8)
    
    # Добавляем разделительную линию и заголовки
    for j in range(num_samples):
        axes[9, j].axhline(y=1, color='red', linewidth=2)
    
    plt.suptitle('Conditional Generation: Generated (Top) vs Real (Bottom) Images', 
                fontsize=16, y=0.95)
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()

# Альтернативный вариант: side-by-side сравнение
def generate_side_by_side_comparison(model, dataset, num_samples=5):
    """Сравнение сгенерированных и реальных изображений бок о бок"""
    model.eval()
    
    real_examples = get_real_examples(dataset, num_samples)
    
    fig, axes = plt.subplots(10, num_samples * 2, figsize=(num_samples * 2, 10))
    
    with torch.no_grad():
        for label in range(10):
            # Генерируем изображения
            z = torch.randn(num_samples, latent_dim).to(device)
            labels_tensor = torch.tensor([label] * num_samples).to(device)
            generated = model.decode(z, labels_tensor).cpu().numpy()
            
            real_images = real_examples[label]
            
            for j in range(num_samples):
                # Сгенерированные изображения
                ax_gen = axes[label, j * 2]
                ax_gen.imshow(generated[j, 0], cmap='gray', vmin=-1, vmax=1)
                ax_gen.axis('off')
                if j == 0:
                    ax_gen.set_ylabel(class_names[label], rotation=0, ha='right', va='center')
                
                # Реальные изображения
                ax_real = axes[label, j * 2 + 1]
                real_img = real_images[j].squeeze().numpy()
                ax_real.imshow(real_img, cmap='gray', vmin=-1, vmax=1)
                ax_real.axis('off')
            
            # Добавляем подписи для первого ряда
            if label == 0:
                for j in range(num_samples):
                    axes[label, j * 2].set_title('Generated', fontsize=8)
                    axes[label, j * 2 + 1].set_title('Real', fontsize=8)
    
    plt.suptitle('Side-by-Side Comparison: Generated vs Real Images', fontsize=16)
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()

# Визуализация интерполяции между классами
def show_class_interpolation(model, num_interpolations=5):
    """Показывает интерполяцию между разными классами"""
    model.eval()
    
    fig, axes = plt.subplots(10, num_interpolations, figsize=(num_interpolations, 10))
    
    with torch.no_grad():
        for source_class in range(10):
            for i in range(num_interpolations):
                # Интерполяция между source_class и следующим классом
                target_class = (source_class + 1) % 10
                
                # Интерполяция latent space
                z_source = torch.randn(1, latent_dim).to(device)
                z_target = torch.randn(1, latent_dim).to(device)
                
                alpha = i / (num_interpolations - 1)
                z_interp = (1 - alpha) * z_source + alpha * z_target
                
                # Интерполяция меток
                label_interp = torch.tensor([source_class]).to(device)
                
                generated = model.decode(z_interp, label_interp)
                generated = generated.cpu().numpy()
                
                ax = axes[source_class, i]
                ax.imshow(generated[0, 0], cmap='gray', vmin=-1, vmax=1)
                ax.axis('off')
                
                if i == 0:
                    ax.set_ylabel(f'{class_names[source_class]}', 
                                rotation=0, ha='right', va='center')
                
                if source_class == 0:
                    ax.set_title(f'α={alpha:.1f}', fontsize=8)
    
    plt.suptitle('Latent Space Interpolation between Classes', fontsize=16)
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()

# Обучение модели
print("Начало обучения Conditional VAE...")
train_losses, val_losses = [], []
train_recon_losses, val_recon_losses = [], []
train_kl_losses, val_kl_losses = [], []

for epoch in range(epochs):
    train_loss, train_recon, train_kl = train(model, train_loader, optimizer, epoch)
    val_loss, val_recon, val_kl = validate(model, test_loader)
    
    train_losses.append(train_loss)
    val_losses.append(val_loss)
    train_recon_losses.append(train_recon)
    val_recon_losses.append(val_recon)
    train_kl_losses.append(train_kl)
    val_kl_losses.append(val_kl)
    
    print(f'Epoch {epoch+1}/{epochs}:')
    print(f'  Train Loss: {train_loss:.4f} (Recon: {train_recon:.4f}, KL: {train_kl:.4f})')
    print(f'  Val Loss: {val_loss:.4f} (Recon: {val_recon:.4f}, KL: {val_kl:.4f})')
    print()

# Визуализация процесса обучения
plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
plt.plot(train_losses, label='Train')
plt.plot(val_losses, label='Validation')
plt.title('Total Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.subplot(1, 3, 2)
plt.plot(train_recon_losses, label='Train')
plt.plot(val_recon_losses, label='Validation')
plt.title('Reconstruction Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.subplot(1, 3, 3)
plt.plot(train_kl_losses, label='Train')
plt.plot(val_kl_losses, label='Validation')
plt.title('KL Divergence')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.tight_layout()
plt.show()

# Генерация изображений с сравнением
print("Генерация условных изображений с сравнением...")
generate_conditionally_with_comparison(model, test_dataset, num_samples=10)

print("Side-by-side сравнение...")
generate_side_by_side_comparison(model, test_dataset, num_samples=5)

print("Интерполяция между классами...")
show_class_interpolation(model, num_interpolations=5)

# Реконструкция примеров
def show_reconstructions(model, dataloader, num_examples=10):
    model.eval()
    data_iter = iter(dataloader)
    images, labels = next(data_iter)
    
    images = images[:num_examples].to(device)
    labels = labels[:num_examples].to(device)
    
    with torch.no_grad():
        reconstructions, _, _ = model(images, labels)
    
    fig, axes = plt.subplots(3, num_examples, figsize=(num_examples, 3))
    
    for i in range(num_examples):
        # Оригиналы
        axes[0, i].imshow(images[i].cpu().squeeze(), cmap='gray')
        axes[0, i].set_title(f'Class: {class_names[labels[i].item()]}', fontsize=8)
        axes[0, i].axis('off')
        
        # Реконструкции
        axes[1, i].imshow(reconstructions[i].cpu().squeeze(), cmap='gray')
        axes[1, i].axis('off')
        
        # Разница
        diff = torch.abs(images[i] - reconstructions[i]).cpu().squeeze()
        axes[2, i].imshow(diff, cmap='hot')
        axes[2, i].axis('off')
    
    axes[0, 0].set_ylabel('Original')
    axes[1, 0].set_ylabel('Reconstructed')
    axes[2, 0].set_ylabel('Difference')
    
    plt.suptitle('Original vs Reconstructed Images with Difference Map')
    plt.tight_layout()
    plt.show()

print("\nДемонстрация реконструкций...")
show_reconstructions(model, test_loader)

# Анализ качества генерации по классам
def analyze_generation_quality(model, dataset):
    """Анализирует качество генерации для каждого класса"""
    model.eval()
    
    print("\nАнализ качества генерации по классам:")
    print("-" * 50)
    
    with torch.no_grad():
        for class_id in range(10):
            # Берем реальные примеры этого класса
            real_images = []
            for img, label in dataset:
                if label == class_id and len(real_images) < 100:
                    real_images.append(img)
                if len(real_images) >= 100:
                    break
            
            real_images = torch.stack(real_images).to(device)
            labels = torch.tensor([class_id] * len(real_images)).to(device)
            
            # Реконструируем
            reconstructions, _, _ = model(real_images, labels)
            
            # Вычисляем MSE между реальными и реконструированными
            mse = F.mse_loss(reconstructions, real_images).item()
            
            print(f"{class_names[class_id]:15} | MSE: {mse:.4f}")

analyze_generation_quality(model, test_dataset)

# Сохранение модели
torch.save({
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'config': {
        'latent_dim': latent_dim,
        'label_embedding_dim': label_embedding_dim
    }
}, 'conditional_vae_fashion_mnist.pth')

print("\nОбучение завершено! Модель сохранена.")
