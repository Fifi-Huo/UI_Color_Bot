import { GetServerSideProps } from 'next';
import { useTranslation } from 'next-i18next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Head from 'next/head';

import { ColorAnalysisPage } from '@/components/ColorAnalysis/ColorAnalysisPage';

export default function ColorAnalysis() {
  const { t } = useTranslation('common');

  return (
    <>
      <Head>
        <title>颜色分析 - UI Color Bot</title>
        <meta
          name="description"
          content="AI驱动的图片颜色分析工具，提取主要颜色并生成专业配色方案"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <ColorAnalysisPage />
    </>
  );
}

export const getServerSideProps: GetServerSideProps = async ({ locale }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale ?? 'en', [
        'common',
        'chat',
        'sidebar',
      ])),
    },
  };
};
