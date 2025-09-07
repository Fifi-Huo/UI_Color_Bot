import React, { useState } from 'react';
import { ImageUpload } from './ImageUpload';
import AccessibilityChecker from './AccessibilityChecker';
import { toast } from 'react-hot-toast';
import { ColorAnalysisNav } from '../Navigation/ColorAnalysisNav';
import { IconPalette, IconEye, IconAccessible, IconDownload, IconPhoto, IconColorSwatch } from '@tabler/icons-react';

interface ColorInfo {
  hex_code: string;
  rgb: number[];
  percentage: number;
  color_name: string;
}

interface ColorAnalysisResult {
  success: boolean;
  colors: ColorInfo[];
  total_colors_found: number;
  processing_time_ms: number;
  algorithm_used: string;
  image_dimensions: { width: number; height: number };
}

interface PaletteResult {
  colors: string[];
  harmony_score: number;
  usage_suggestions: string[];
  palette_type: string;
}

export const ColorAnalysisPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'analysis' | 'accessibility'>('analysis');
  const [analysisResult, setAnalysisResult] = useState<ColorAnalysisResult | null>(null);
  const [paletteResults, setPaletteResults] = useState<any[]>([]);
  const [generatedPalettes, setGeneratedPalettes] = useState<Record<string, PaletteResult>>({});
  const [annotatedImage, setAnnotatedImage] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isGeneratingAnnotation, setIsGeneratingAnnotation] = useState(false);
  const [accessibilityResults, setAccessibilityResults] = useState<any[]>([]);
  const [isCheckingAccessibility, setIsCheckingAccessibility] = useState(false);
  const [pickedColors, setPickedColors] = useState<any[]>([]);
  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGeneratingPalettes, setIsGeneratingPalettes] = useState(false);
  const [isAnnotating, setIsAnnotating] = useState(false);

  const handleColorPicked = (color: any) => {
    setPickedColors(prev => [...prev, color]);
    toast.success(`已取色: ${color.hex}`);
  };

  const handleAnalysisComplete = async (result: ColorAnalysisResult, imageUrl: string) => {
    setAnalysisResult(result);
    setCurrentImageUrl(imageUrl);
    
    // 自动生成配色方案
    if (result.colors.length > 0) {
      await generatePalettes(result.colors[0].hex_code);
      
      // 自动生成标注图
      await generateAnnotatedImage(imageUrl, result.colors);
      
      // 自动检查颜色可访问性
      await checkColorsAccessibility(result.colors);
    }
  };

  const generateAnnotatedImage = async (imageUrl: string, colors: any[]) => {
    setIsAnnotating(true);
    try {
      const response = await fetch('/api/annotate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_url: imageUrl,
          colors: colors.map(color => ({
            hex: color.hex_code,
            rgb: color.rgb,
            proportion: color.percentage
          }))
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAnnotatedImage(data.annotated_image);
        toast.success('颜色标注图生成成功！');
      } else {
        toast.error('生成标注图失败');
      }
    } catch (error) {
      console.error('Error generating annotated image:', error);
      toast.error('生成标注图时出错');
    } finally {
      setIsAnnotating(false);
    }
  };

  const generatePalettes = async (baseColor: string) => {
    setIsGeneratingPalettes(true);
    try {
      const paletteTypes = ['monochromatic', 'complementary', 'triadic', 'analogous'];
      const palettes: Record<string, PaletteResult> = {};

      for (const type of paletteTypes) {
        const response = await fetch('/api/generate-palette', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            base_color: baseColor,
            scheme: type,
            num_colors: 5
          }),
        });

        if (response.ok) {
          const data = await response.json();
          // 转换后端返回的颜色对象数组为字符串数组
          const paletteData = data.palette;
          if (paletteData && paletteData.colors) {
            palettes[type] = {
              ...paletteData,
              colors: paletteData.colors.map((color: any) => 
                typeof color === 'string' ? color : color.hex_code
              )
            };
          }
        }
      }

      setGeneratedPalettes(palettes);
    } catch (error) {
      console.error('Failed to generate palettes:', error);
    } finally {
      setIsGeneratingPalettes(false);
    }
  };

  const checkColorsAccessibility = async (colors: ColorInfo[]) => {
    setIsCheckingAccessibility(true);
    try {
      const results = [];
      
      // 检查所有颜色对的对比度
      for (let i = 0; i < colors.length; i++) {
        for (let j = i + 1; j < colors.length; j++) {
          const foreground = colors[i].hex_code;
          const background = colors[j].hex_code;
          
          const response = await fetch('/api/check-accessibility', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              foreground_color: foreground,
              background_color: background,
              text_size: 'normal',
              wcag_level: 'AA',
              check_color_blindness: true
            }),
          });

          if (response.ok) {
            const data = await response.json();
            results.push({
              foreground,
              background,
              foregroundName: colors[i].color_name,
              backgroundName: colors[j].color_name,
              ...data
            });
          }
        }
      }
      
      setAccessibilityResults(results);
      toast.success(`已完成 ${results.length} 个颜色对的可访问性检查`);
    } catch (error) {
      console.error('Error checking accessibility:', error);
      toast.error('可访问性检查失败');
    } finally {
      setIsCheckingAccessibility(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportPalette = (colors: string[], name: string) => {
    const paletteData = {
      name,
      colors,
      timestamp: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(paletteData, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name}-palette.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <ColorAnalysisNav />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            颜色分析工具
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            上传图片分析颜色，或检查颜色可访问性
          </p>
        </div>

        {/* 标签页导航 */}
        <div className="flex justify-center mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-1 shadow-sm">
            <button
              onClick={() => setActiveTab('analysis')}
              className={`px-6 py-3 rounded-md font-medium transition-colors ${
                activeTab === 'analysis'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <IconPhoto className="w-5 h-5" />
                图片颜色分析
              </div>
            </button>
            <button
              onClick={() => setActiveTab('accessibility')}
              className={`px-6 py-3 rounded-md font-medium transition-colors ${
                activeTab === 'accessibility'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <IconAccessible className="w-5 h-5" />
                可访问性检查
              </div>
            </button>
          </div>
        </div>

        {/* 标签页内容 */}
        {activeTab === 'analysis' && (
          <>
            {/* Image Upload */}
            <div className="mb-8">
              <ImageUpload 
                onAnalysisComplete={handleAnalysisComplete}
                onColorPicked={handleColorPicked}
              />
            </div>
          </>
        )}

        {activeTab === 'accessibility' && (
          <div className="mb-8">
            <AccessibilityChecker />
          </div>
        )}

        {/* 图片分析结果 - 只在分析标签页显示 */}
        {activeTab === 'analysis' && (
          <>
            {/* Analysis Progress */}
            {(isAnalyzing || isGeneratingPalettes || isAnnotating || isCheckingAccessibility) && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
                  <div className="text-gray-700 dark:text-gray-300">
                    {isAnalyzing && "正在分析图片颜色..."}
                    {isGeneratingPalettes && "正在生成配色方案..."}
                    {isAnnotating && "正在生成颜色标注图..."}
                    {isCheckingAccessibility && "正在检查颜色可访问性..."}
                  </div>
                </div>
              </div>
            )}

            {/* Color Palette Panel */}
            {analysisResult && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <IconPalette className="mr-2" size={24} />
                    提取颜色色板
                  </h2>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      共 {analysisResult.total_colors_found} 种颜色
                    </span>
                    {currentImageUrl && (
                      <button
                        onClick={() => generateAnnotatedImage(currentImageUrl, analysisResult.colors)}
                        disabled={isAnnotating}
                        className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                      >
                        {isAnnotating ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            生成中...
                          </>
                        ) : (
                          <>
                            <IconEye className="mr-2" size={16} />
                            生成标注图
                          </>
                        )}
                      </button>
                    )}
                    <button
                      onClick={() => checkColorsAccessibility(analysisResult.colors)}
                      disabled={isCheckingAccessibility}
                      className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                    >
                      {isCheckingAccessibility ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          检查中...
                        </>
                      ) : (
                        <>
                          <IconAccessible className="mr-2" size={16} />
                          可访问性检查
                        </>
                      )}
                    </button>
                  </div>
                </div>
            
            {/* Color Palette Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 mb-6">
              {analysisResult.colors.map((color: ColorInfo, index: number) => (
                <div key={index} className="group relative">
                  {/* Color Block */}
                  <div
                    className="w-full h-24 rounded-lg border-2 border-gray-200 dark:border-gray-600 cursor-pointer transition-all duration-200 hover:scale-105 hover:shadow-lg"
                    style={{ backgroundColor: color.hex_code }}
                    onClick={() => copyToClipboard(color.hex_code)}
                    title={`点击复制 ${color.hex_code}`}
                  />
                  
                  {/* Color Info */}
                  <div className="mt-2 text-center">
                    <div className="text-sm font-mono font-medium text-gray-900 dark:text-white">
                      {color.hex_code}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      RGB({color.rgb.join(', ')})
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-500">
                      {(color.percentage * 100).toFixed(1)}%
                    </div>
                  </div>
                  
                  {/* Hover Tooltip */}
                  <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
                    {color.color_name}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Color Palette Actions */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => {
                    const hexColors = analysisResult.colors.map(c => c.hex_code).join(', ');
                    copyToClipboard(hexColors);
                    toast.success('所有HEX颜色已复制到剪贴板');
                  }}
                  className="flex items-center px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <IconDownload className="mr-2" size={14} />
                  复制所有HEX
                </button>
                
                <button
                  onClick={() => {
                    const rgbColors = analysisResult.colors.map(c => `rgb(${c.rgb.join(', ')})`).join(', ');
                    copyToClipboard(rgbColors);
                    toast.success('所有RGB颜色已复制到剪贴板');
                  }}
                  className="flex items-center px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors"
                >
                  <IconDownload className="mr-2" size={14} />
                  复制所有RGB
                </button>
                
                <button
                  onClick={() => {
                    const paletteData = {
                      name: `Color Palette - ${new Date().toLocaleDateString()}`,
                      colors: analysisResult.colors.map(color => ({
                        hex: color.hex_code,
                        rgb: color.rgb,
                        name: color.color_name,
                        percentage: color.percentage
                      })),
                      metadata: {
                        total_colors: analysisResult.total_colors_found,
                        processing_time: analysisResult.processing_time_ms,
                        algorithm: analysisResult.algorithm_used,
                        image_dimensions: analysisResult.image_dimensions,
                        created_at: new Date().toISOString()
                      }
                    };
                    
                    const blob = new Blob([JSON.stringify(paletteData, null, 2)], {
                      type: 'application/json',
                    });
                    
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `color-palette-${Date.now()}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                    toast.success('色板数据已导出');
                  }}
                  className="flex items-center px-3 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <IconDownload className="mr-2" size={14} />
                  导出色板
                </button>
              </div>
              
              <div className="text-sm text-gray-600 dark:text-gray-400">
                处理时间: {analysisResult.processing_time_ms.toFixed(1)}ms | 
                算法: {analysisResult.algorithm_used} | 
                尺寸: {analysisResult.image_dimensions.width} × {analysisResult.image_dimensions.height}
              </div>
            </div>
          </div>
        )}

            {/* Generated Palettes */}
            {(Object.keys(generatedPalettes).length > 0 || isGeneratingPalettes) && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <IconPalette className="mr-2" size={24} />
                    AI 生成配色方案
                  </h2>
                  {isGeneratingPalettes && (
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      正在生成配色方案...
                    </div>
                  )}
                </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Object.entries(generatedPalettes).map(([type, palette]: [string, PaletteResult]) => (
                <div key={type} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-medium text-gray-900 dark:text-white capitalize">
                      {type.replace('_', ' ')}
                    </h3>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => copyToClipboard(palette.colors.join(', '))}
                        className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
                      >
                        复制
                      </button>
                      <button
                        onClick={() => exportPalette(palette.colors, type)}
                        className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                      >
                        <IconDownload size={12} />
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 mb-3">
                    {palette.colors.map((color: string, index: number) => (
                      <div key={index} className="flex-1">
                        <div
                          className="h-12 rounded cursor-pointer border border-gray-200 dark:border-gray-600"
                          style={{ backgroundColor: color }}
                          onClick={() => copyToClipboard(color)}
                          title={`点击复制 ${color}`}
                        />
                        <p className="text-xs text-center mt-1 text-gray-600 dark:text-gray-300">
                          {color}
                        </p>
                      </div>
                    ))}
                  </div>
                  
                  <div className="text-sm text-gray-600 dark:text-gray-300">
                    <p>和谐度: {(palette.harmony_score * 100).toFixed(0)}%</p>
                    {palette.usage_suggestions.length > 0 && (
                      <p className="mt-1">建议: {palette.usage_suggestions[0]}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

            {/* Annotated Image */}
            {annotatedImage && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <IconPalette className="mr-2" size={24} />
                    颜色标注图
                  </h2>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = annotatedImage;
                        link.download = 'color-annotated-image.png';
                        link.click();
                      }}
                      className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <IconDownload className="mr-2" size={16} />
                      下载标注图
                    </button>
                    {currentImageUrl && analysisResult && (
                      <button
                        onClick={() => generateAnnotatedImage(currentImageUrl, analysisResult.colors)}
                        disabled={isAnnotating}
                        className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                      >
                        {isAnnotating ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            重新生成中...
                          </>
                        ) : (
                          <>
                            <IconPalette className="mr-2" size={16} />
                            重新生成
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
            
            <div className="flex flex-col items-center">
              <div className="w-full max-w-4xl">
                <img 
                  src={annotatedImage} 
                  alt="颜色标注图" 
                  className="w-full h-auto rounded-lg shadow-lg border border-gray-200 dark:border-gray-600"
                />
              </div>
              
              <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg w-full max-w-4xl">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">标注图说明</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
                    <span className="text-gray-700 dark:text-gray-300">右侧布局设计</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
                    <span className="text-gray-700 dark:text-gray-300">颜色按占比排序</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-purple-500 rounded mr-2"></div>
                    <span className="text-gray-700 dark:text-gray-300">引导线连接</span>
                  </div>
                </div>
                <p className="mt-3 text-gray-600 dark:text-gray-400">
                  标注图展示了图片中的主要颜色区域，右侧显示颜色信息包括HEX值、RGB值和占比。
                  细线连接原图中的颜色区域到右侧的颜色块，便于理解颜色分布。
                </p>
              </div>
            </div>
          </div>
            )}

            {/* Accessibility Analysis Results */}
            {accessibilityResults.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <IconAccessible className="mr-2" size={24} />
                    颜色可访问性分析
                  </h2>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    共检查 {accessibilityResults.length} 个颜色对
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {accessibilityResults.map((result, index) => (
                    <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      {/* Color Pair Display */}
                      <div className="flex items-center gap-4 mb-4">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-8 h-8 rounded border border-gray-300"
                            style={{ backgroundColor: result.foreground }}
                          />
                          <span className="text-sm font-medium">{result.foreground}</span>
                        </div>
                        <span className="text-gray-400">vs</span>
                        <div className="flex items-center gap-2">
                          <div
                            className="w-8 h-8 rounded border border-gray-300"
                            style={{ backgroundColor: result.background }}
                          />
                          <span className="text-sm font-medium">{result.background}</span>
                        </div>
                      </div>
                      
                      {/* Contrast Ratio */}
                      <div className="mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            对比度: {result.contrast_result?.ratio?.toFixed(2)}:1
                          </span>
                          <div className="flex gap-2">
                            {result.contrast_result?.passes_aa_normal && (
                              <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                                AA ✓
                              </span>
                            )}
                            {result.contrast_result?.passes_aaa_normal && (
                              <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                                AAA ✓
                              </span>
                            )}
                            {!result.contrast_result?.passes_aa_normal && (
                              <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                                不合规
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Color Blindness Check */}
                      {result.colorblindness_results && result.colorblindness_results.length > 0 && (
                        <div className="mb-3">
                          <span className="text-sm text-gray-600 dark:text-gray-300">
                            色盲友好性: {result.colorblindness_results.some((cb: any) => cb.passes_wcag) ? '✓ 友好' : '✗ 不友好'}
                          </span>
                        </div>
                      )}
                      
                      {/* Recommendations */}
                      {result.recommendations && result.recommendations.length > 0 && (
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          <strong>建议:</strong> {result.recommendations[0]}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Summary Stats */}
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-lg font-semibold text-blue-600">
                        {accessibilityResults.filter(r => r.contrast_result?.passes_aa_normal).length}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">WCAG AA 合规</div>
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-blue-600">
                        {accessibilityResults.filter(r => r.contrast_result?.passes_aaa_normal).length}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">WCAG AAA 合规</div>
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-blue-600">
                        {accessibilityResults.filter(r => r.colorblindness_results?.some((cb: any) => cb.passes_wcag)).length}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">色盲友好</div>
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-blue-600">
                        {Math.round((accessibilityResults.reduce((sum, r) => sum + (r.contrast_result?.ratio || 0), 0) / accessibilityResults.length) * 100) / 100}:1
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">平均对比度</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Color Details */}
            {analysisResult && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <IconEye className="mr-2" size={24} />
                    颜色详细信息
                  </h2>
                  
                  {!annotatedImage && (
                    <button
                      onClick={() => generateAnnotatedImage('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800', analysisResult.colors)}
                      disabled={isAnnotating}
                      className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isAnnotating ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          生成中...
                        </>
                      ) : (
                        <>
                          <IconPalette className="mr-2" size={16} />
                          生成标注图
                        </>
                      )}
                    </button>
                  )}
                </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {analysisResult.colors.map((color: ColorInfo, index: number) => (
                <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div
                    className="w-full h-20 rounded-lg mb-3 border border-gray-200 dark:border-gray-600"
                    style={{ backgroundColor: color.hex_code }}
                  />
                  
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">HEX:</span>
                      <span 
                        className="ml-2 cursor-pointer text-blue-600 dark:text-blue-400 hover:underline"
                        onClick={() => copyToClipboard(color.hex_code)}
                      >
                        {color.hex_code}
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">RGB:</span>
                      <span 
                        className="ml-2 cursor-pointer text-blue-600 dark:text-blue-400 hover:underline"
                        onClick={() => copyToClipboard(`rgb(${color.rgb.join(', ')})`)}
                      >
                        {color.rgb.join(', ')}
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">占比:</span>
                      <span className="ml-2 text-gray-600 dark:text-gray-300">
                        {(color.percentage * 100).toFixed(1)}%
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">类型:</span>
                      <span className="ml-2 text-gray-600 dark:text-gray-300">
                        {color.color_name}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
