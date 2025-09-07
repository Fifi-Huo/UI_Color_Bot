import React, { useState, useRef, useCallback } from 'react';
import { IconPhoto, IconUpload, IconPalette, IconX, IconEye } from '@tabler/icons-react';
import toast from 'react-hot-toast';

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

interface PickedColor {
  hex: string;
  rgb: number[];
  color_name: string;
  position: { x: number; y: number };
  accessibility?: {
    wcag_aa_normal: boolean;
    wcag_aa_large: boolean;
    wcag_aaa_normal: boolean;
    wcag_aaa_large: boolean;
    contrast_ratio: number;
    color_blind_safe: boolean;
    recommendations: string[];
  };
}

interface ImageUploadProps {
  onAnalysisComplete?: (result: ColorAnalysisResult, imageUrl: string) => void;
  onColorPicked?: (color: any) => void;
  className?: string;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({ onAnalysisComplete, onColorPicked, className = '' }) => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<ColorAnalysisResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [isPickingColor, setIsPickingColor] = useState(false);
  const [pickedColors, setPickedColors] = useState<PickedColor[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  // 可访问性分析函数
  const analyzeColorAccessibility = async (hexColor: string) => {
    try {
      const response = await fetch('/api/accessibility-check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          colors: [hexColor, '#FFFFFF'] // 与白色背景对比
        }),
      });

      const data = await response.json();
      
      if (data.success && data.results && data.results.length > 0) {
        const result = data.results[0];
        return {
          wcag_aa_normal: result.wcag_aa_normal || false,
          wcag_aa_large: result.wcag_aa_large || false,
          wcag_aaa_normal: result.wcag_aaa_normal || false,
          wcag_aaa_large: result.wcag_aaa_large || false,
          contrast_ratio: result.contrast_ratio || 0,
          color_blind_safe: result.color_blind_safe || false,
          recommendations: result.recommendations || []
        };
      }
      return null;
    } catch (error) {
      console.error('Accessibility analysis error:', error);
      return null;
    }
  };

  const compressImage = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        // 计算压缩后的尺寸，保持宽高比
        const maxWidth = 1200;
        const maxHeight = 1200;
        let { width, height } = img;
        
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height;
            height = maxHeight;
          }
        }
        
        canvas.width = width;
        canvas.height = height;
        
        // 绘制压缩后的图片
        ctx?.drawImage(img, 0, 0, width, height);
        
        // 转换为base64，质量设为0.8
        const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.8);
        resolve(compressedDataUrl);
      };
      
      img.src = URL.createObjectURL(file);
    });
  };

  const handleFileSelect = async (file: File) => {
    if (file.size > 50 * 1024 * 1024) { // 50MB limit for original file
      toast.error('文件大小不能超过50MB');
      return;
    }

    try {
      const compressedImage = await compressImage(file);
      setSelectedImage(compressedImage);
      // 等待状态更新后再分析颜色
      setTimeout(() => analyzeColors(), 100);
    } catch (error) {
      toast.error('图片处理失败，请重试');
    }
  };

  const handleImageSelect = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) {
      toast.error('请选择图片文件');
      return;
    }

    await handleFileSelect(file);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImageSelect(file);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleImageSelect(file);
    }
  }, [handleImageSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  }, []);

  const analyzeColors = async () => {
    if (!selectedImage) return;
    
    setIsAnalyzing(true);
    try {
      const response = await fetch('/api/analyze-colors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_url: selectedImage,
          num_colors: 5,
          min_percentage: 0.05
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setAnalysisResult(data);
        onAnalysisComplete?.(data, selectedImage);
        toast.success(`成功提取 ${data.total_colors_found} 种主要颜色`);
      } else {
        toast.error(data.error || '颜色分析失败');
      }
    } catch (error) {
      console.error('Color analysis error:', error);
      toast.error('颜色分析失败，请重试');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleImageClick = async (e: React.MouseEvent<HTMLImageElement>) => {
    if (!isPickingColor || !selectedImage || !imageRef.current) return;

    const rect = imageRef.current.getBoundingClientRect();
    const x = Math.round((e.clientX - rect.left) * (imageRef.current.naturalWidth / rect.width));
    const y = Math.round((e.clientY - rect.top) * (imageRef.current.naturalHeight / rect.height));

    try {
      const response = await fetch('/api/pick-color', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_url: selectedImage,
          x: x,
          y: y
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        // 为取色结果添加可访问性分析
        const colorWithAccessibility = await analyzeColorAccessibility(data.color.hex);
        
        const newColor: PickedColor = {
          hex: data.color.hex,
          rgb: data.color.rgb,
          color_name: data.color.color_name,
          position: { x, y },
          accessibility: colorWithAccessibility || undefined
        };
        
        setPickedColors(prev => [...prev, newColor]);
        onColorPicked?.(newColor);
        toast.success(`取色成功: ${data.color.hex}`);
      } else {
        toast.error(data.error || '取色失败');
      }
    } catch (error) {
      console.error('Pick color error:', error);
      toast.error('取色请求失败');
    }
  };

  const toggleColorPicking = () => {
    setIsPickingColor(!isPickingColor);
    if (!isPickingColor) {
      toast.success('点击图片上的任意位置来取色');
    }
  };

  const clearPickedColors = () => {
    setPickedColors([]);
    toast.success('已清除所有取色点');
  };

  const clearImage = () => {
    setSelectedImage(null);
    setAnalysisResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={`w-full max-w-2xl mx-auto ${className}`}>
      {/* Upload Area */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${dragActive 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }
          ${selectedImage ? 'border-solid' : ''}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileInput}
          className="hidden"
        />

        {selectedImage ? (
          <div className="space-y-4">
            <div className="relative inline-block">
              <img
                ref={imageRef}
                src={selectedImage}
                alt="Selected"
                className={`max-w-full max-h-64 rounded-lg shadow-md ${
                  isPickingColor ? 'cursor-crosshair' : 'cursor-default'
                }`}
                onClick={handleImageClick}
              />
              <button
                onClick={clearImage}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
              >
                <IconX size={16} />
              </button>
              
              {/* 显示取色点 */}
              {pickedColors.map((color, index) => (
                <div
                  key={index}
                  className="absolute w-4 h-4 border-2 border-white rounded-full shadow-lg"
                  style={{
                    backgroundColor: color.hex,
                    left: `${(color.position.x / (imageRef.current?.naturalWidth || 1)) * 100}%`,
                    top: `${(color.position.y / (imageRef.current?.naturalHeight || 1)) * 100}%`,
                    transform: 'translate(-50%, -50%)'
                  }}
                />
              ))}
            </div>
            
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                onClick={analyzeColors}
                disabled={isAnalyzing}
                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <IconPalette className="mr-2" size={20} />
                {isAnalyzing ? '分析中...' : '分析颜色'}
              </button>
              
              <button
                onClick={toggleColorPicking}
                className={`inline-flex items-center px-4 py-2 rounded-lg transition-colors ${
                  isPickingColor
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                <IconEye className="mr-2" size={16} />
                {isPickingColor ? '取色模式 (开启)' : '点击取色'}
              </button>
              
              {pickedColors.length > 0 && (
                <button
                  onClick={clearPickedColors}
                  className="inline-flex items-center px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/30"
                >
                  <IconX className="mr-2" size={16} />
                  清除取色点
                </button>
              )}
            </div>
            
            {/* 显示取色结果 */}
            {pickedColors.length > 0 && (
              <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                  取色结果 ({pickedColors.length})
                </h4>
                <div className="space-y-3">
                  {pickedColors.map((color, index) => (
                    <div
                      key={index}
                      className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600"
                    >
                      <div className="flex items-start space-x-3">
                        <div
                          className="w-12 h-12 rounded-lg border border-gray-200 dark:border-gray-600 flex-shrink-0"
                          style={{ backgroundColor: color.hex }}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <p className="text-sm font-mono font-medium text-gray-900 dark:text-gray-100">
                              {color.hex}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              RGB({color.rgb.join(', ')})
                            </p>
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-300 mb-2">
                            {color.color_name}
                          </p>
                          
                          {/* 可访问性信息 */}
                          {color.accessibility && (
                            <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                              <h5 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                                可访问性分析 (与白色背景对比)
                              </h5>
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div className="space-y-1">
                                  <div className="flex items-center space-x-1">
                                    <span className={`w-2 h-2 rounded-full ${color.accessibility.wcag_aa_normal ? 'bg-green-500' : 'bg-red-500'}`} />
                                    <span className="text-gray-600 dark:text-gray-400">WCAG AA 普通文本</span>
                                  </div>
                                  <div className="flex items-center space-x-1">
                                    <span className={`w-2 h-2 rounded-full ${color.accessibility.wcag_aa_large ? 'bg-green-500' : 'bg-red-500'}`} />
                                    <span className="text-gray-600 dark:text-gray-400">WCAG AA 大文本</span>
                                  </div>
                                </div>
                                <div className="space-y-1">
                                  <div className="flex items-center space-x-1">
                                    <span className={`w-2 h-2 rounded-full ${color.accessibility.wcag_aaa_normal ? 'bg-green-500' : 'bg-red-500'}`} />
                                    <span className="text-gray-600 dark:text-gray-400">WCAG AAA 普通文本</span>
                                  </div>
                                  <div className="flex items-center space-x-1">
                                    <span className={`w-2 h-2 rounded-full ${color.accessibility.color_blind_safe ? 'bg-green-500' : 'bg-yellow-500'}`} />
                                    <span className="text-gray-600 dark:text-gray-400">色盲友好</span>
                                  </div>
                                </div>
                              </div>
                              <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                                对比度: {color.accessibility.contrast_ratio.toFixed(2)}:1
                              </div>
                              {color.accessibility.recommendations.length > 0 && (
                                <div className="mt-2">
                                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">建议:</p>
                                  <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                                    {color.accessibility.recommendations.slice(0, 2).map((rec, i) => (
                                      <li key={i} className="flex items-start">
                                        <span className="mr-1">•</span>
                                        <span>{rec}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <IconPhoto className="mx-auto text-gray-400" size={48} />
            <div>
              <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                上传图片进行颜色分析
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                拖拽图片到此处或点击选择文件
              </p>
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <IconUpload className="mr-2" size={16} />
              选择图片
            </button>
            <p className="text-xs text-gray-400">
              支持 JPG, PNG, GIF 格式，最大 10MB
            </p>
          </div>
        )}
      </div>

      {/* Analysis Results */}
      {analysisResult && (
        <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              颜色分析结果
            </h3>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              处理时间: {analysisResult.processing_time_ms.toFixed(1)}ms
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {analysisResult.colors.map((color, index) => (
              <div
                key={index}
                className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div
                  className="w-12 h-12 rounded-lg shadow-sm border border-gray-200 dark:border-gray-600"
                  style={{ backgroundColor: color.hex_code }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {color.hex_code}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {color.color_name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {(color.percentage * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
            <p>图片尺寸: {analysisResult.image_dimensions.width} × {analysisResult.image_dimensions.height}</p>
            <p>算法: {analysisResult.algorithm_used}</p>
          </div>
        </div>
      )}
    </div>
  );
};
