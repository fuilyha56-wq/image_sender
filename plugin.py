"""image_sender 插件 - 发送图片消息"""

from typing import Annotated

from src.app.plugin_system.base import BasePlugin, register_plugin
from src.core.components.base.action import BaseAction


@register_plugin
class ImageSenderPlugin(BasePlugin):
    """发送图片消息插件"""

    plugin_name = "image_sender"
    plugin_description = "发送图片消息的插件"
    plugin_version = "1.0.0"

    configs: list[type] = []
    dependent_components: list[str] = []

    def get_components(self) -> list[type]:
        return [SendImageAction]


class SendImageAction(BaseAction):
    """发送图片消息"""

    action_name = "send_image"
    action_description = "发送一张图片给用户。可以传入base64数据或文件路径。适用于发送截图、照片等。注意：不要发送包含敏感信息（密码、隐私、银行信息等）的图片。"

    associated_types: list[str] = ["image"]
    chatter_allow: list[str] = []

    async def execute(
        self,
        image_data: Annotated[str | None, "图片数据，base64编码"] = None,
        file_path: Annotated[str | None, "图片文件路径，如 data/screenshots/xxx.png"] = None,
        processed_plain_text: Annotated[str | None, "图片的文本描述，可为空"] = None,
    ) -> tuple[bool, str]:
        """发送图片消息

        Args:
            image_data: 图片的base64数据
            file_path: 图片文件路径
            processed_plain_text: 图片的文本描述
        """
        from src.app.plugin_system.api.send_api import send_image
        from pathlib import Path

        # 优先使用file_path
        if file_path:
            try:
                path = Path(file_path)
                if not path.exists():
                    return False, f"文件不存在: {file_path}"
                
                # 安全检查：只允许发送 data/screenshots/ 目录下的最新截图（5分钟内）
                screenshots_dir = Path("data/screenshots")
                if not (screenshots_dir in path.parents or path.parent == screenshots_dir):
                    return False, "只允许发送 data/screenshots 目录下的截图"
                
                # 检查文件修改时间，5分钟内的才算新
                import time
                file_age = time.time() - path.stat().st_mtime
                if file_age > 300:  # 5分钟
                    return False, f"截图已过期（超过5分钟），请重新截图"
                
                image_data = path.read_bytes()
                # 转换为base64
                import base64
                image_data = base64.b64encode(image_data).decode('utf-8')
            except Exception as e:
                return False, f"读取文件失败: {e}"

        if not image_data:
            return False, "图片数据为空"

        text = processed_plain_text or "[图片]"
        success = await send_image(
            image_data=image_data,
            stream_id=self.chat_stream.stream_id,
            platform=self.chat_stream.platform,
            processed_plain_text=text,
        )

        if success:
            return True, f"已发送图片: {text}"
        return False, "图片发送失败"