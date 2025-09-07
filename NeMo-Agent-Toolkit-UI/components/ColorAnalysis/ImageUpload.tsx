import React, { useState, useRef, useCallback } from 'react';
import { IconPhoto, IconUpload, IconX, IconPalette, IconEye } from '@tabler/icons-react';
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

interface Props {
  onAnalysisComplete?: (result: ColorAnalysisResult, imageUrl: string) => void;
  className?: string;
}

export const ImageUpload: React.FC<Props> = ({ onAnalysisComplete, className = '' }) => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<ColorAnalysisResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    if (!selectedImage) {
      toast.error('请先选择图片');
      return;
    }

    setIsAnalyzing(true);
    try {
      // Convert base64 to blob and upload to a temporary URL service
      // For demo purposes, we'll use the image directly as base64
      const response = await fetch('/api/color-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: selectedImage,
          num_colors: 5
        }),
      });

      if (!response.ok) {
        throw new Error('颜色分析失败');
      }

      const result: ColorAnalysisResult = await response.json();
      setAnalysisResult(result);
      onAnalysisComplete?.(result, selectedImage!);
      toast.success(`成功提取${result.total_colors_found}种主要颜色`);
    } catch (error) {
      console.error('Color analysis error:', error);
      toast.error('颜色分析失败，请重试');
    } finally {
      setIsAnalyzing(false);
    }
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
                src={selectedImage}
                alt="Selected"
                className="max-w-full max-h-64 rounded-lg shadow-md"
              />
              <button
                onClick={clearImage}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
              >
                <IconX size={16} />
              </button>
            </div>
            
            <button
              onClick={analyzeColors}
              disabled={isAnalyzing}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <IconPalette className="mr-2" size={20} />
              {isAnalyzing ? '分析中...' : '分析颜色'}
            </button>
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
