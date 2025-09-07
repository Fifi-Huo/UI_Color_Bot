import React, { useState } from 'react';
import { IconEye, IconEyeOff, IconCheck, IconX, IconAlertTriangle, IconCopy } from '@tabler/icons-react';
import toast from 'react-hot-toast';

interface ContrastResult {
  ratio: number;
  passes_aa_normal: boolean;
  passes_aa_large: boolean;
  passes_aaa_normal: boolean;
  passes_aaa_large: boolean;
  grade: string;
}

interface ColorBlindnessResult {
  type: string;
  simulated_foreground: string;
  simulated_background: string;
  contrast_ratio: number;
  passes_wcag: boolean;
}

interface AccessibilityResult {
  success: boolean;
  foreground_color: string;
  background_color: string;
  contrast_result: ContrastResult;
  colorblindness_results: ColorBlindnessResult[];
  recommendations: string[];
  processing_time_ms: number;
}

const AccessibilityChecker: React.FC = () => {
  const [foregroundColor, setForegroundColor] = useState('#000000');
  const [backgroundColor, setBackgroundColor] = useState('#FFFFFF');
  const [textSize, setTextSize] = useState<'normal' | 'large'>('normal');
  const [wcagLevel, setWcagLevel] = useState<'AA' | 'AAA'>('AA');
  const [result, setResult] = useState<AccessibilityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showColorBlindness, setShowColorBlindness] = useState(true);

  const checkAccessibility = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/check-accessibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          foreground_color: foregroundColor,
          background_color: backgroundColor,
          text_size: textSize,
          wcag_level: wcagLevel,
          check_colorblind: showColorBlindness
        })
      });

      if (!response.ok) {
        throw new Error('检查失败');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Accessibility check error:', error);
      toast.error('可访问性检查失败');
    } finally {
      setLoading(false);
    }
  };

  const copyColor = (color: string) => {
    navigator.clipboard.writeText(color);
    toast.success(`已复制颜色: ${color}`);
  };

  const getGradeIcon = (grade: string) => {
    switch (grade) {
      case 'AAA':
        return <IconCheck className="w-5 h-5 text-green-600" />;
      case 'AA':
        return <IconCheck className="w-5 h-5 text-blue-600" />;
      case 'AA Large':
        return <IconAlertTriangle className="w-5 h-5 text-yellow-600" />;
      default:
        return <IconX className="w-5 h-5 text-red-600" />;
    }
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'AAA':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'AA':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'AA Large':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-red-600 bg-red-50 border-red-200';
    }
  };

  const colorBlindnessNames: Record<string, string> = {
    protanopia: '红色盲',
    deuteranopia: '绿色盲',
    tritanopia: '蓝色盲',
    achromatopsia: '全色盲'
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center gap-2 mb-6">
        <IconEye className="w-6 h-6 text-blue-600" />
        <h2 className="text-xl font-semibold text-gray-900">可访问性检查</h2>
      </div>

      {/* 颜色选择器 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            前景色 (文字颜色)
          </label>
          <div className="flex items-center gap-3">
            <input
              type="color"
              value={foregroundColor}
              onChange={(e) => setForegroundColor(e.target.value)}
              className="w-12 h-12 rounded border border-gray-300 cursor-pointer"
            />
            <input
              type="text"
              value={foregroundColor}
              onChange={(e) => setForegroundColor(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="#000000"
            />
            <button
              onClick={() => copyColor(foregroundColor)}
              className="p-2 text-gray-500 hover:text-gray-700"
            >
              <IconCopy className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            背景色
          </label>
          <div className="flex items-center gap-3">
            <input
              type="color"
              value={backgroundColor}
              onChange={(e) => setBackgroundColor(e.target.value)}
              className="w-12 h-12 rounded border border-gray-300 cursor-pointer"
            />
            <input
              type="text"
              value={backgroundColor}
              onChange={(e) => setBackgroundColor(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="#FFFFFF"
            />
            <button
              onClick={() => copyColor(backgroundColor)}
              className="p-2 text-gray-500 hover:text-gray-700"
            >
              <IconCopy className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 预览区域 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          颜色预览
        </label>
        <div
          className="p-6 rounded-lg border-2 border-dashed border-gray-300"
          style={{ backgroundColor: backgroundColor }}
        >
          <p
            className="text-lg font-medium"
            style={{ color: foregroundColor }}
          >
            这是示例文本，用于预览颜色对比效果
          </p>
          <p
            className="text-sm mt-2"
            style={{ color: foregroundColor }}
          >
            小号文本示例 - 检查在不同文字大小下的可读性
          </p>
        </div>
      </div>

      {/* 设置选项 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            文字大小
          </label>
          <select
            value={textSize}
            onChange={(e) => setTextSize(e.target.value as 'normal' | 'large')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="normal">普通文字 (&lt;18pt)</option>
            <option value="large">大号文字 (≥18pt)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            WCAG 标准
          </label>
          <select
            value={wcagLevel}
            onChange={(e) => setWcagLevel(e.target.value as 'AA' | 'AAA')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="AA">AA 级别 (最低要求)</option>
            <option value="AAA">AAA 级别 (增强要求)</option>
          </select>
        </div>

        <div className="flex items-end">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={showColorBlindness}
              onChange={(e) => setShowColorBlindness(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">色盲友好性检查</span>
          </label>
        </div>
      </div>

      {/* 检查按钮 */}
      <button
        onClick={checkAccessibility}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? '检查中...' : '检查可访问性'}
      </button>

      {/* 结果展示 */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* 对比度结果 */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">对比度分析</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {result.contrast_result.ratio.toFixed(2)}:1
                </div>
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border ${getGradeColor(result.contrast_result.grade)}`}>
                  {getGradeIcon(result.contrast_result.grade)}
                  <span className="font-medium">{result.contrast_result.grade}</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">AA 普通文字 (4.5:1)</span>
                  {result.contrast_result.passes_aa_normal ? (
                    <IconCheck className="w-5 h-5 text-green-600" />
                  ) : (
                    <IconX className="w-5 h-5 text-red-600" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">AA 大号文字 (3:1)</span>
                  {result.contrast_result.passes_aa_large ? (
                    <IconCheck className="w-5 h-5 text-green-600" />
                  ) : (
                    <IconX className="w-5 h-5 text-red-600" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">AAA 普通文字 (7:1)</span>
                  {result.contrast_result.passes_aaa_normal ? (
                    <IconCheck className="w-5 h-5 text-green-600" />
                  ) : (
                    <IconX className="w-5 h-5 text-red-600" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">AAA 大号文字 (4.5:1)</span>
                  {result.contrast_result.passes_aaa_large ? (
                    <IconCheck className="w-5 h-5 text-green-600" />
                  ) : (
                    <IconX className="w-5 h-5 text-red-600" />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 色盲友好性结果 */}
          {showColorBlindness && result.colorblindness_results.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">色盲友好性</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.colorblindness_results.map((cbResult, index) => (
                  <div key={index} className="bg-white rounded-lg p-4 border">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">
                        {colorBlindnessNames[cbResult.type] || cbResult.type}
                      </h4>
                      {cbResult.passes_wcag ? (
                        <IconCheck className="w-5 h-5 text-green-600" />
                      ) : (
                        <IconX className="w-5 h-5 text-red-600" />
                      )}
                    </div>
                    
                    <div className="flex items-center gap-3 mb-2">
                      <div
                        className="w-6 h-6 rounded border"
                        style={{ backgroundColor: cbResult.simulated_background }}
                      />
                      <div
                        className="w-6 h-6 rounded border"
                        style={{ backgroundColor: cbResult.simulated_foreground }}
                      />
                      <span className="text-sm text-gray-600">
                        {cbResult.contrast_ratio.toFixed(2)}:1
                      </span>
                    </div>
                    
                    <div
                      className="p-2 rounded text-sm"
                      style={{
                        backgroundColor: cbResult.simulated_background,
                        color: cbResult.simulated_foreground
                      }}
                    >
                      模拟效果预览
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 建议 */}
          {result.recommendations.length > 0 && (
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">改进建议</h3>
              <ul className="space-y-2">
                {result.recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
                    <span className="text-gray-700">{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 处理时间 */}
          <div className="text-sm text-gray-500 text-center">
            处理时间: {result.processing_time_ms.toFixed(1)}ms
          </div>
        </div>
      )}
    </div>
  );
};

export default AccessibilityChecker;
