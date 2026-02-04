<template>
  <div class="poi-manage" style="display: flex; gap: 20px; height: calc(100vh - 40px);">
    <!-- 左侧地图区域 -->
    <div style="flex: 2; border: 1px solid #eee; border-radius: 8px; overflow: hidden; position: relative;">
      <MapContainer :height="'100%'" @map-click="handleMapClick" />
      <!-- 点击选点提示 -->
      <div v-if="showPointTip" style="position: absolute; top: 20px; left: 20px; background: rgba(255,255,255,0.9); padding: 8px 16px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
        已选点：{{ currentPoint.lng.toFixed(6) }}, {{ currentPoint.lat.toFixed(6) }}
      </div>
    </div>
    <!-- 右侧操作区域 -->
    <div style="flex: 1; display: flex; flex-direction: column; gap: 20px;">
      <!-- 筛选栏 -->
      <el-card shadow="hover">
        <el-select v-model="filterType" placeholder="按POI类型筛选" style="width: 100%;">
          <el-option label="全部POI" value="" />
          <el-option label="入口" value="entrance" />
          <el-option label="景点" value="view" />
          <el-option label="休息区" value="rest" />
          <el-option label="出口" value="exit" />
        </el-select>
      </el-card>
      <!-- 表单录入 -->
      <el-card shadow="hover" title="POI信息录入">
        <el-form :model="poiForm" label-width="80px" @submit.prevent="handleSubmit">
          <el-form-item label="POI名称" required>
            <el-input v-model="poiForm.name" placeholder="请输入POI名称" />
          </el-form-item>
          <el-form-item label="POI类型" required>
            <el-select v-model="poiForm.type" placeholder="请选择POI类型">
              <el-option label="入口" value="entrance" />
              <el-option label="景点" value="view" />
              <el-option label="休息区" value="rest" />
              <el-option label="出口" value="exit" />
            </el-select>
          </el-form-item>
          <el-form-item label="POI描述">
            <el-input v-model="poiForm.desc" type="textarea" rows="3" placeholder="请输入POI描述" />
          </el-form-item>
          <el-form-item label="状态">
            <el-switch v-model="poiForm.status" active-text="启用" inactive-text="禁用" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSubmit" :disabled="!currentPoint.lng">提交</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
      <!-- POI列表 -->
      <el-card shadow="hover" title="POI列表" style="flex: 1; overflow: auto;">
        <el-table :data="filterPoiList" border stripe style="width: 100%;">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="type" label="类型">
            <template #default="scope">
              <el-tag :type="tagTypeMap[scope.row.type as PoiType]">{{ typeNameMap[scope.row.type as PoiType] }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <el-switch v-model="scope.row.status" @change="handleToggleStatus(scope.row.id)" />
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" width="180" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button type="text" @click="handleEdit(scope.row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import MapContainer from '@/components/map/MapContainer.vue';
import { useAdminStore } from '@/store';
// 修复2：从map.ts导入LngLat（已导出），保留admin.ts的PoiInfo
import type { PoiInfo } from '@/types/admin';
import type { LngLat } from '@/types/map';

// 修复1：定义POI类型联合类型，约束映射对象和POI.type的取值范围
type PoiType = 'entrance' | 'view' | 'rest' | 'exit';

const store = useAdminStore();
// 修复1：为映射对象添加严格TS类型注解，指定键为PoiType，值为对应类型
const typeNameMap: Record<PoiType, string> = { entrance: '入口', view: '景点', rest: '休息区', exit: '出口' };
const tagTypeMap: Record<PoiType, 'primary' | 'danger' | 'success' | 'info'> = { entrance: 'primary', view: 'danger', rest: 'success', exit: 'info' };

// 当前选点
const currentPoint = ref<LngLat>({ lng: 0, lat: 0 });
const showPointTip = ref(false);
// 筛选类型：约束为PoiType或空字符串（匹配下拉选择值）
const filterType = ref<PoiType | ''>('');
// 表单数据
const poiForm = ref<Omit<PoiInfo, 'id' | 'createTime'>>({
  name: '',
  type: 'entrance',
  lng: 0,
  lat: 0,
  desc: '',
  status: true
});
// 编辑状态标记
const isEdit = ref(false);
const editId = ref(0);

// 地图点击选点
const handleMapClick = (e: { lng: number; lat: number; pixel: [number, number] }) => {
  currentPoint.value = { lng: e.lng, lat: e.lat };
  poiForm.value.lng = e.lng;
  poiForm.value.lat = e.lat;
  showPointTip.value = true;
  ElMessage.info('已选择地图点位，可填写信息提交');
};

// 筛选后的POI列表
const filterPoiList = computed(() => {
  if (!filterType.value) return store.poiList;
  return store.poiList.filter(poi => poi.type === filterType.value);
});

// 提交表单
const handleSubmit = () => {
  if (!poiForm.value.name) return ElMessage.warning('请输入POI名称');
  if (!poiForm.value.lng || !poiForm.value.lat) return ElMessage.warning('请先在地图选择点位');
  
  if (isEdit.value) {
    // 编辑POI
    store.editPoi({ ...poiForm.value, id: editId.value, createTime: new Date().toLocaleString() });
    isEdit.value = false;
    ElMessage.success('POI编辑成功');
  } else {
    // 添加POI
    store.addPoi(poiForm.value);
    ElMessage.success('POI添加成功');
  }
  handleReset();
};

// 重置表单
const handleReset = () => {
  poiForm.value = { name: '', type: 'entrance', lng: 0, lat: 0, desc: '', status: true };
  currentPoint.value = { lng: 0, lat: 0 };
  showPointTip.value = false;
  isEdit.value = false;
  editId.value = 0;
};

// 切换POI状态
const handleToggleStatus = (id: number) => {
  store.togglePoiStatus(id);
  ElMessage.success('POI状态切换成功');
};

// 编辑POI
const handleEdit = (poi: PoiInfo) => {
  isEdit.value = true;
  editId.value = poi.id;
  poiForm.value = { ...poi };
  currentPoint.value = { lng: poi.lng, lat: poi.lat };
  showPointTip.value = true;
  // 滚动到表单区域
  document.querySelector('.el-card__header')?.scrollIntoView({ behavior: 'smooth' });
  ElMessage.info('进入POI编辑模式，请修改信息后提交');
};

onMounted(() => {
  // 初始化地图后，渲染已有POI（后续在MapContainer中扩展POI渲染方法）
  console.log('已有POI列表：', store.poiList);
});
</script>

<style scoped>
.poi-manage {
  flex: 1;
}
/* 修复选点提示定位问题 */
:deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
:deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}
:deep(.el-table) {
  flex: 1;
}
</style>