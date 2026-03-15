"""
人脸识别模块 - 提供真正的人脸特征提取和比对功能
"""
import numpy as np
from PIL import Image
import io
import base64
import json

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("⚠️ 未安装 face_recognition 库，请运行：pip install face_recognition")


def extract_face_encoding(image_data):
    """
    从图像数据中提取人脸特征向量
    
    Args:
        image_data: 可以是 PIL Image、numpy array 或 base64 字符串
        
    Returns:
        list: 128 维人脸特征向量，如果检测不到人脸则返回 None
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return None
    
    try:
        # 如果是 base64 字符串，转换为 PIL Image
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            base64_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes))
        elif isinstance(image_data, str):
            image = Image.open(image_data)
        else:
            image = image_data
        
        # 转换为 numpy array（face_recognition 需要 RGB 格式）
        image_array = np.array(image)
        
        # 如果是 RGBA 格式，转换为 RGB
        if len(image_array.shape) == 3 and image_array.shape[2] == 4:
            image_array = image_array[:, :, :3]
        
        # 使用 face_recognition 提取人脸特征
        face_locations = face_recognition.face_locations(image_array, model='hog')
        
        if not face_locations:
            return None
        
        # 提取第一个检测到的人脸特征
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if face_encodings:
            return face_encodings[0].tolist()
        
        return None
        
    except Exception as e:
        print(f"提取人脸特征失败：{e}")
        return None


def verify_face_match(known_encoding, current_image_data, tolerance=0.6):
    """
    验证当前人脸是否与注册的人脸匹配
    
    Args:
        known_encoding: 已注册的人脸特征向量（128 维列表）
        current_image_data: 当前拍摄的图像数据
        tolerance: 相似度阈值，默认 0.6（越小越严格）
        
    Returns:
        tuple: (是否匹配，相似度分数，距离)
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return False, 0.0, 999.0
    
    try:
        # 从当前图像提取特征
        current_encoding = extract_face_encoding(current_image_data)
        
        if current_encoding is None:
            return False, 0.0, 999.0
        
        # 计算欧氏距离（越小越相似）
        known_array = np.array(known_encoding)
        current_array = np.array(current_encoding)
        
        distance = float(np.linalg.norm(known_array - current_array))
        
        # 计算相似度（0-1 之间）
        similarity = 1.0 / (1.0 + distance)
        
        # 判断是否匹配
        is_match = distance <= tolerance
        
        return is_match, similarity, distance
        
    except Exception as e:
        print(f"人脸比对失败：{e}")
        return False, 0.0, 999.0


def extract_and_average_encodings(image_data_list):
    """
    从多张图像中提取人脸特征并计算平均值（提高准确性）
    
    Args:
        image_data_list: 图像数据列表
        
    Returns:
        list: 平均后的 128 维人脸特征向量，如果失败则返回 None
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return None
    
    encodings = []
    for img_data in image_data_list:
        encoding = extract_face_encoding(img_data)
        if encoding:
            encodings.append(encoding)
    
    if not encodings:
        return None
    
    # 计算平均特征向量
    avg_encoding = np.mean(encodings, axis=0).tolist()
    return avg_encoding


if __name__ == "__main__":
    # 测试代码
    print("人脸识别模块已加载")
    print(f"face_recognition 库状态：{'可用' if FACE_RECOGNITION_AVAILABLE else '不可用'}")
