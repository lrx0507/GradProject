<template>
  <div class="admin-dashboard" style="height: calc(100vh - 40px); display: flex; flex-direction: column; gap: 20px;">
    <!-- 关键指标卡片 -->
    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
      <el-card shadow="hover" style="flex: 1; min-width: 200px;">
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: bold; color: #1890ff; margin: 10px 0;">{{ store.statData.poiTotal }}</div>
          <div style="font-size: 16px; color: #666;">总POI数量</div>
        </div>
      </el-card>
      <el-card shadow="hover" style="flex: 1; min-width: 200px;">
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: bold; color: #f56c6c; margin: 10px 0;">{{ store.statData.roadTotal }}</div>
          <div style="font-size: 16px; color: #666;">路网边总数</div>
        </div>
      </el-card>
      <el-card shadow="hover" style="flex: 1; min-width: 200px;">
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: bold; color: #67c23a; margin: 10px 0;">{{ (store.statData.roadTotalLength / 1000).toFixed(2) }}</div>
          <div style="font-size: 16px; color: #666;">路网总长度(km)</div>
        </div>
      </el-card>
      <el-card shadow="hover" style="flex: 1; min-width: 200px;">
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: bold; color: #909399; margin: 10px 0;">{{ store.isolatedPoi.length }}</div>
          <div style="font-size: 16px; color: #666;">孤立POI数量</div>
        </div>
      </el-card>
      <el-card shadow="hover" style="flex: 1; min-width: 200px;">
        <div style="text-align: center;">
          <div style="font-size: 32px; font-weight: bold; color: #faad14; margin: 10px 0;">{{ store.config.featureRoutes.length }}</div>
          <div style="font-size: 16px; color: #666;">特色路线数量</div>
        </div>
      </el-card>
    </div>
    <!-- 图表区域 -->
    <div style="display: flex; gap: 20px; flex: 1; min-height: 300px;">
      <!-- POI类型分布饼图 -->
      <el-card shadow="hover" style="flex: 1;">
        <template #header>
          <div class="card-header">
            <span>POI类型分布</span>
          </div>
        </template>
        <div id="poiPieChart" style="width: 100%; height: 300px;"></div>
      </el-card>
      <!-- 路网长度趋势图（简化，模拟近7天） -->
      <el-card shadow="hover" style="flex: 1;">
        <template #header>
          <div class="card-header">
            <span>路网长度增长趋势(近7天)</span>
          </div>
        </template>
        <div id="roadTrendChart" style="width: 100%; height: 300px;"></div>
      </el-card>
    </div>
    <!-- 最近操作日志 -->
    <el-card shadow="hover" style="flex: 1; min-height: 200px; overflow: auto;">
      <template #header>
        <div class="card-header">
          <span>最近操作日志（10条）</span>
        </div>
      </template>
      <el-table :data="store.statData.recentLogs" border stripe style="width: 100%;">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="type" label="操作类型" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.type === 'add' ? 'success' : scope.row.type === 'edit' ? 'primary' : scope.row.type === 'delete' ? 'danger' : 'info'">
              {{ typeNameMap[scope.row.type as LogType] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="操作内容" />
        <el-table-column prop="time" label="操作时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// 修复4：补充导入onUnmounted；修复3：删除未使用的ref
import { onMounted, onUnmounted } from 'vue';
import { useAdminStore } from '@/store';
// 引入ECharts
import * as echarts from 'echarts';

const store = useAdminStore();

// 修复2：1.定义操作类型联合类型，约束合法取值；2.为映射对象添加严格TS类型注解
type LogType = 'add' | 'edit' | 'delete' | 'config';
const typeNameMap: Record<LogType, string> = { add: '添加', edit: '编辑', delete: '删除', config: '配置' };

// ECharts实例
let poiPieChart: echarts.ECharts | null = null;
let roadTrendChart: echarts.ECharts | null = null;

// 初始化图表
const initCharts = () => {
  // 1. POI类型分布饼图
  const poiPieDom = document.getElementById('poiPieChart');
  if (poiPieDom) {
    poiPieChart = echarts.init(poiPieDom);
    const option = {
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [
        {
          name: 'POI类型',
          type: 'pie',
          radius: '60%',
          data: [
            { value: store.statData.poiCount.entrance, name: '入口' },
            { value: store.statData.poiCount.view, name: '景点' },
            { value: store.statData.poiCount.rest, name: '休息区' },
            { value: store.statData.poiCount.exit, name: '出口' }
          ],
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
          },
          color: ['#1890ff', '#f56c6c', '#67c23a', '#909399']
        }
      ]
    };
    poiPieChart.setOption(option);
  }

  // 2. 路网长度增长趋势图（模拟近7天数据）
  const roadTrendDom = document.getElementById('roadTrendChart');
  if (roadTrendDom) {
    roadTrendChart = echarts.init(roadTrendDom);
    // 模拟近7天日期
    const dates = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - 6 + i);
      return date.getMonth() + 1 + '/' + date.getDate();
    });
    // 模拟增长数据（基于总长度）
    const total = store.statData.roadTotalLength / 1000;
    const data = dates.map((_, i) => (total / 7) * (i + 1)).map(v => Number(v.toFixed(2)));
    const option = {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', boundaryGap: false, data: dates },
      yAxis: { type: 'value', name: '长度(km)' },
      series: [
        {
          name: '路网长度',
          type: 'line',
          data: data,
          smooth: true,
          lineStyle: { color: '#f56c6c', width: 2 },
          itemStyle: { color: '#f56c6c' },
          areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(245,108,108,0.3)' }, { offset: 1, color: 'rgba(245,108,108,0)' }]) }
        }
      ]
    };
    roadTrendChart.setOption(option);
  }
};

// 窗口大小变化时重绘图表
const resizeCharts = () => {
  poiPieChart?.resize();
  roadTrendChart?.resize();
};

onMounted(() => {
  // 初始化图表
  initCharts();
  // 监听窗口大小变化
  window.addEventListener('resize', resizeCharts);
});

// 页面卸载时销毁图表
onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts);
  poiPieChart?.dispose();
  roadTrendChart?.dispose();
});
</script>

<style scoped>
.admin-dashboard {
  flex: 1;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>