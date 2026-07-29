"""图片生成服务的统一异常。"""


class ImageGenerationError(RuntimeError):
    """图片生成模块的基础异常。"""


class ImageGenerationConfigurationError(ImageGenerationError):
    """图片生成服务配置缺失或无效。"""


class ImageGenerationNetworkError(ImageGenerationError):
    """图片生成或下载时发生网络错误。"""


class ImageGenerationResponseError(ImageGenerationError):
    """图片供应商返回错误或无效内容。"""
