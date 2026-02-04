<template>
  <div class="elevation-profile" ref="chartRef" :style="{ height, width }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as echarts from 'echarts';
import type { ElevationProfileProps } from '@/types/chart';

// Props + TS类型 + 默认值（Vue自动注入API，无需导入）
const props = withDefaults(defineProps<ElevationProfileProps>(), {
  width: '100%',
  height: '300px',
  title: '路径高程/坡度剖面图',
  elevationColor: '#1890ff',
  slopeColor: '#f56c6c'
});

// 图表实例（TS严格类型定义）
const chartRef = ref<HTMLDivElement | null>(null);
const chartInstance = ref<echarts.ECharts | null>(null);

// 初始化图表
const initChart = (): void => {
  // 前置校验：容器不存在/无数据时不初始化
  if (!chartRef.value || props.data.length === 0) return;
  chartInstance.value = echarts.init(chartRef.value);
  
  // 提取图表数据（严格基于props.data类型，无任何ECharts类型依赖）
  const distanceData = props.data.map(item => item.distance_m);
  const elevationData = props.data.map(item => item.elevation_m);
  const slopeData = props.data.map(item => item.slope_deg);

  // ECharts配置项：使用TS原生unknown规避所有ECharts类型依赖
  const option = {
    title: { text: props.title, left: 'center', textStyle: { fontSize: 14, fontWeight: 500 } },
    tooltip: {
      trigger: 'axis',
      // 核心：用unknown替代any，配合原生JS校验，满足TS+ESLint双严格
      formatter: (params: unknown) => {
        // 原生JS类型校验：确保params是数组、有数据、有有效索引
        if (
          !params || 
          !Array.isArray(params) || 
          params.length === 0 || 
          !params[0] || 
          typeof params[0].dataIndex !== 'number' || 
          !distanceData[params[0].dataIndex]
        ) {
          return '';
        }
        // 确定类型后赋值，无任何TS/ESLint报错
        const index = params[0].dataIndex;
        const distance = distanceData[index]!.toFixed(2) + '米';
        const elevation = (params[0].value as number).toFixed(2) + '米';
        const slope = params[1] ? (params[1].value as number).toFixed(2) + '度' : '0.00度';
        return `${distance}<br/>高程：${elevation}<br/>坡度：${slope}`;
      }
    },
    legend: { data: ['高程', '坡度'], top: 30, left: 'center' },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'value', 
      name: '距起点距离（米）', 
      nameTextStyle: { fontSize: 12 },
      axisLabel: { formatter: '{value} 米' }
    },
    yAxis: [
      {
        type: 'value',
        name: '高程（米）',
        nameTextStyle: { color: props.elevationColor, fontSize: 12 },
        axisLabel: { color: props.elevationColor, fontSize: 12 }
      },
      {
        type: 'value',
        name: '坡度（度）',
        nameTextStyle: { color: props.slopeColor, fontSize: 12 },
        axisLabel: { color: props.slopeColor, fontSize: 12 },
        min: 0,
        max: 30
      }
    ],
    series: [
      {
        name: '高程',
        type: 'line',
        yAxisIndex: 0,
        data: elevationData,
        lineStyle: { color: props.elevationColor, width: 2 },
        itemStyle: { color: props.elevationColor },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: props.elevationColor + '80' },
            { offset: 1, color: props.elevationColor + '10' }
          ])
        },
        smooth: true
      },
      {
        name: '坡度',
        type: 'line',
        yAxisIndex: 1,
        data: slopeData,
        lineStyle: { color: props.slopeColor, width: 2 },
        itemStyle: { color: props.slopeColor },
        smooth: true
      }
    ],
    responsive: true
  };

  // 直接传入配置项，无需ECharts类型约束
  chartInstance.value.setOption(option);
};

// 图表自适应
const resizeChart = (): void => {
  if (chartInstance.value) {
    chartInstance.value.resize();
  }
};

// 监听数据/配置变化，重新渲染图表
watch([() => props.data, () => props.title, () => props.elevationColor, () => props.slopeColor], () => {
  if (chartInstance.value) {
    chartInstance.value.dispose();
    initChart();
  }
}, { deep: true });

// 生命周期：挂载时初始化，卸载时销毁
onMounted(() => {
  initChart();
  window.addEventListener('resize', resizeChart);
});

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose();
    chartInstance.value = null;
  }
  window.removeEventListener('resize', resizeChart);
});

// 暴露组件方法（Vue自动注入API）
defineExpose({
  chartRef,
  chartInstance,
  resizeChart,
  initChart
});
</script>

<style scoped>
.elevation-profile {
  width: v-bind(width);
  height: v-bind(height);
  min-height: 200px;
  box-sizing: border-box;
}
</style>