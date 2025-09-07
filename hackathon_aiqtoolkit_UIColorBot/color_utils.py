#!/usr/bin/env python3
"""
颜色工具模块
提供专业的UI颜色分析和建议功能
"""

import colorsys
import re
from typing import List, Dict, Tuple, Optional

class ColorUtils:
    """颜色工具类"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """十六进制颜色转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """RGB转十六进制颜色"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
        """RGB转HSL"""
        r, g, b = r/255.0, g/255.0, b/255.0
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return h*360, s*100, l*100
    
    @staticmethod
    def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
        """HSL转RGB"""
        h, s, l = h/360.0, s/100.0, l/100.0
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return int(r*255), int(g*255), int(b*255)
    
    @staticmethod
    def get_contrast_ratio(color1: str, color2: str) -> float:
        """计算两个颜色的对比度"""
        def get_luminance(hex_color: str) -> float:
            r, g, b = ColorUtils.hex_to_rgb(hex_color)
            r, g, b = [x/255.0 for x in (r, g, b)]
            
            # 应用gamma校正
            r = r/12.92 if r <= 0.03928 else pow((r+0.055)/1.055, 2.4)
            g = g/12.92 if g <= 0.03928 else pow((g+0.055)/1.055, 2.4)
            b = b/12.92 if b <= 0.03928 else pow((b+0.055)/1.055, 2.4)
            
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        lum1 = get_luminance(color1)
        lum2 = get_luminance(color2)
        
        # 确保较亮的颜色在分子
        if lum1 > lum2:
            return (lum1 + 0.05) / (lum2 + 0.05)
        else:
            return (lum2 + 0.05) / (lum1 + 0.05)
    
    @staticmethod
    def generate_color_palette(base_color: str, scheme: str = "complementary") -> List[str]:
        """生成配色方案"""
        r, g, b = ColorUtils.hex_to_rgb(base_color)
        h, s, l = ColorUtils.rgb_to_hsl(r, g, b)
        
        palette = [base_color]
        
        if scheme == "complementary":
            # 互补色
            comp_h = (h + 180) % 360
            comp_r, comp_g, comp_b = ColorUtils.hsl_to_rgb(comp_h, s, l)
            palette.append(ColorUtils.rgb_to_hex(comp_r, comp_g, comp_b))
            
        elif scheme == "triadic":
            # 三角配色
            for offset in [120, 240]:
                new_h = (h + offset) % 360
                new_r, new_g, new_b = ColorUtils.hsl_to_rgb(new_h, s, l)
                palette.append(ColorUtils.rgb_to_hex(new_r, new_g, new_b))
                
        elif scheme == "analogous":
            # 类似色
            for offset in [-30, 30]:
                new_h = (h + offset) % 360
                new_r, new_g, new_b = ColorUtils.hsl_to_rgb(new_h, s, l)
                palette.append(ColorUtils.rgb_to_hex(new_r, new_g, new_b))
                
        elif scheme == "monochromatic":
            # 单色配色（不同明度）
            for l_offset in [-20, 20, -40, 40]:
                new_l = max(10, min(90, l + l_offset))
                new_r, new_g, new_b = ColorUtils.hsl_to_rgb(h, s, new_l)
                palette.append(ColorUtils.rgb_to_hex(new_r, new_g, new_b))
        
        return palette[:5]  # 限制为5个颜色
    
    @staticmethod
    def get_accessibility_info(bg_color: str, text_color: str) -> Dict[str, any]:
        """获取可访问性信息"""
        contrast = ColorUtils.get_contrast_ratio(bg_color, text_color)
        
        return {
            "contrast_ratio": round(contrast, 2),
            "aa_normal": contrast >= 4.5,
            "aa_large": contrast >= 3.0,
            "aaa_normal": contrast >= 7.0,
            "aaa_large": contrast >= 4.5,
            "recommendation": ColorUtils._get_accessibility_recommendation(contrast)
        }
    
    @staticmethod
    def _get_accessibility_recommendation(contrast: float) -> str:
        """获取可访问性建议"""
        if contrast >= 7.0:
            return "优秀 - 符合AAA标准"
        elif contrast >= 4.5:
            return "良好 - 符合AA标准"
        elif contrast >= 3.0:
            return "一般 - 仅适用于大字体"
        else:
            return "不佳 - 建议调整颜色"
    
    @staticmethod
    def extract_colors_from_text(text: str) -> List[str]:
        """从文本中提取颜色代码"""
        # 匹配十六进制颜色
        hex_pattern = r'#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}'
        colors = re.findall(hex_pattern, text)
        
        # 标准化为6位十六进制
        normalized_colors = []
        for color in colors:
            if len(color) == 4:  # #RGB -> #RRGGBB
                color = f"#{color[1]*2}{color[2]*2}{color[3]*2}"
            normalized_colors.append(color.upper())
        
        return list(set(normalized_colors))  # 去重

class ColorAnalyzer:
    """颜色分析器"""
    
    def __init__(self):
        self.utils = ColorUtils()
    
    def analyze_color_scheme(self, colors: List[str]) -> Dict[str, any]:
        """分析配色方案"""
        if not colors:
            return {"error": "没有提供颜色"}
        
        analysis = {
            "colors": colors,
            "color_count": len(colors),
            "harmony_type": self._detect_harmony_type(colors),
            "accessibility": [],
            "recommendations": []
        }
        
        # 分析每对颜色的对比度
        for i, bg_color in enumerate(colors):
            for j, text_color in enumerate(colors):
                if i != j:
                    accessibility = self.utils.get_accessibility_info(bg_color, text_color)
                    analysis["accessibility"].append({
                        "background": bg_color,
                        "text": text_color,
                        **accessibility
                    })
        
        # 生成建议
        analysis["recommendations"] = self._generate_recommendations(colors)
        
        return analysis
    
    def _detect_harmony_type(self, colors: List[str]) -> str:
        """检测配色和谐类型"""
        if len(colors) < 2:
            return "单色"
        
        # 简化的和谐类型检测
        hues = []
        for color in colors:
            r, g, b = self.utils.hex_to_rgb(color)
            h, s, l = self.utils.rgb_to_hsl(r, g, b)
            hues.append(h)
        
        hue_diff = abs(hues[0] - hues[1]) if len(hues) >= 2 else 0
        
        if hue_diff < 30:
            return "类似色"
        elif 150 <= hue_diff <= 210:
            return "互补色"
        elif 90 <= hue_diff <= 150:
            return "分裂互补色"
        else:
            return "自由配色"
    
    def _generate_recommendations(self, colors: List[str]) -> List[str]:
        """生成配色建议"""
        recommendations = []
        
        if len(colors) == 1:
            recommendations.append("建议添加互补色或类似色来丰富配色方案")
        
        # 检查对比度
        low_contrast_pairs = []
        for i, bg in enumerate(colors):
            for j, text in enumerate(colors):
                if i != j:
                    contrast = self.utils.get_contrast_ratio(bg, text)
                    if contrast < 4.5:
                        low_contrast_pairs.append((bg, text))
        
        if low_contrast_pairs:
            recommendations.append("部分颜色对比度不足，建议调整以提高可读性")
        
        return recommendations

# 测试函数
def test_color_utils():
    """测试颜色工具"""
    utils = ColorUtils()
    analyzer = ColorAnalyzer()
    
    # 测试颜色转换
    print("颜色转换测试:")
    hex_color = "#3498db"
    rgb = utils.hex_to_rgb(hex_color)
    hsl = utils.rgb_to_hsl(*rgb)
    print(f"HEX: {hex_color} -> RGB: {rgb} -> HSL: {hsl}")
    
    # 测试配色方案生成
    print("\n配色方案测试:")
    palette = utils.generate_color_palette(hex_color, "complementary")
    print(f"互补色方案: {palette}")
    
    # 测试对比度
    print("\n对比度测试:")
    contrast = utils.get_contrast_ratio("#000000", "#ffffff")
    print(f"黑白对比度: {contrast}")
    
    # 测试配色分析
    print("\n配色分析测试:")
    analysis = analyzer.analyze_color_scheme(["#3498db", "#e74c3c", "#2ecc71"])
    print(f"分析结果: {analysis['harmony_type']}")

if __name__ == "__main__":
    test_color_utils()
