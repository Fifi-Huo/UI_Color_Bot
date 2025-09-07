import React from 'react';
import Link from 'next/link';
import { IconPalette, IconPhoto, IconEye } from '@tabler/icons-react';

export const ColorAnalysisNav: React.FC = () => {
  return (
    <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-2 text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400">
              <IconPalette size={24} />
              <span className="font-semibold text-lg">UI Color Bot</span>
            </Link>
            
            <nav className="flex space-x-6">
              <Link 
                href="/" 
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                聊天助手
              </Link>
              <Link 
                href="/color-analysis" 
                className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-1"
              >
                <IconPhoto size={16} />
                <span>颜色分析</span>
              </Link>
            </nav>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              AI 驱动的颜色设计助手
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
