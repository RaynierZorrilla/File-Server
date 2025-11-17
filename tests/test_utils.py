"""
Tests para utilidades
"""
import pytest
from pathlib import Path
from app.utils import sha256sum, image_size, make_thumbnail
from PIL import Image
import io


def test_sha256sum():
    """Test cálculo de hash SHA256"""
    data = b"test data"
    hash_result = sha256sum(data)
    
    assert len(hash_result) == 64  # SHA256 produce 64 caracteres hex
    assert isinstance(hash_result, str)
    
    # Verificar que el mismo dato produce el mismo hash
    hash_result2 = sha256sum(data)
    assert hash_result == hash_result2


def test_sha256sum_different_data():
    """Test que diferentes datos producen diferentes hashes"""
    data1 = b"test data 1"
    data2 = b"test data 2"
    
    hash1 = sha256sum(data1)
    hash2 = sha256sum(data2)
    
    assert hash1 != hash2


def test_image_size_valid_image(tmp_path):
    """Test obtener dimensiones de una imagen válida"""
    # Crear una imagen de prueba
    img_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (800, 600), color="red")
    img.save(img_path)
    
    width, height = image_size(img_path)
    
    assert width == 800
    assert height == 600


def test_image_size_invalid_file(tmp_path):
    """Test obtener dimensiones de un archivo inválido"""
    # Crear un archivo que no es imagen
    invalid_path = tmp_path / "test.txt"
    invalid_path.write_text("not an image")
    
    width, height = image_size(invalid_path)
    
    assert width is None
    assert height is None


def test_image_size_nonexistent_file(tmp_path):
    """Test obtener dimensiones de un archivo inexistente"""
    nonexistent_path = tmp_path / "nonexistent.jpg"
    
    width, height = image_size(nonexistent_path)
    
    assert width is None
    assert height is None


def test_make_thumbnail_contain(tmp_path):
    """Test generar thumbnail con modo contain"""
    # Crear imagen de prueba
    src = tmp_path / "source.jpg"
    img = Image.new("RGB", (800, 600), color="blue")
    img.save(src)
    
    dst = tmp_path / "thumbnail.jpg"
    make_thumbnail(src, dst, w=200, h=200, fit="contain")
    
    assert dst.exists()
    
    # Verificar dimensiones
    with Image.open(dst) as thumb:
        assert thumb.width <= 200
        assert thumb.height <= 200
        # Mantiene aspect ratio
        assert abs((thumb.width / thumb.height) - (800 / 600)) < 0.1


def test_make_thumbnail_crop(tmp_path):
    """Test generar thumbnail con modo crop"""
    # Crear imagen de prueba
    src = tmp_path / "source.jpg"
    img = Image.new("RGB", (800, 600), color="green")
    img.save(src)
    
    dst = tmp_path / "thumbnail.jpg"
    make_thumbnail(src, dst, w=200, h=200, fit="crop")
    
    assert dst.exists()
    
    # Verificar dimensiones exactas
    with Image.open(dst) as thumb:
        assert thumb.width == 200
        assert thumb.height == 200


def test_make_thumbnail_auto_size(tmp_path):
    """Test generar thumbnail sin especificar tamaño"""
    # Crear imagen de prueba
    src = tmp_path / "source.jpg"
    img = Image.new("RGB", (800, 600), color="yellow")
    img.save(src)
    
    dst = tmp_path / "thumbnail.jpg"
    make_thumbnail(src, dst, w=None, h=None, fit="contain")
    
    assert dst.exists()
    
    # Debería usar tamaño por defecto (320)
    with Image.open(dst) as thumb:
        assert thumb.width <= 320 or thumb.height <= 320

