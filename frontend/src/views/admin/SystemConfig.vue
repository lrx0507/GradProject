<template>
  <div class="system-config" style="display: flex; gap: 20px; height: calc(100vh - 40px);">
    <!-- 左侧基础配置 -->
    <el-card shadow="hover" style="flex: 1;">
      <h3 style="margin: 0 0 20px 0; padding-bottom: 10px; border-bottom: 1px solid #eee;">基础参数配置</h3>
      <el-form :model="configForm" label-width="120px" @submit.prevent="handleSaveBaseConfig">
        <el-form-item label="坡度权重α" required>
          <el-slider
            v-model="configForm.slopeWeight"
            :min="0"
            :max="1"
            :step="0.01"
            style="width: 80%; display: inline-block; margin-right: 20px;"
          />
          <el-input
            v-model.number="configForm.slopeWeight"
            style="width: 100px; display: inline-block;"
            :min="0"
            :max="1"
            step="0.01"
          />
          <div style="font-size: 12px; color: #666; margin-top: 8px;">
            说明：α越大，路径规划越优先考虑坡度（0≤α≤1）
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSaveBaseConfig">保存基础配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <!-- 右侧特色路线配置 -->
    <el-card shadow="hover" style="flex: 2;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h3 style="margin: 0;">特色路线配置</h3>
        <el-button type="primary" @click="showAddRouteDialog = true">添加特色路线</el-button>
      </div>
      <!-- 特色路线列表 -->
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px;">
        <div v-for="route in store.config.featureRoutes" :key="route.id" style="border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
          <!-- 封面图 -->
          <div style="height: 180px; background: #f5f7fa; display: flex; align-items: center; justify-content: center; position: relative;">
            <img v-if="route.cover" :src="route.cover" alt="路线封面" style="width: 100%; height: 100%; object-fit: cover;" />
            <div v-else style="color: #909399; text-align: center;">
              <el-icon size="40"><Picture /></el-icon>
              <p>暂无封面图</p>
            </div>
            <el-button 
              type="text" 
              style="position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.5); color: #fff;"
              @click.stop="handleUploadCover(route.id)"
            >
              更换封面
            </el-button>
          </div>
          <!-- 路线信息 -->
          <div style="padding: 15px;">
            <h4 style="margin: 0 0 10px 0;">{{ route.name }}</h4>
            <p style="font-size: 12px; color: #666; margin: 0 0 15px 0; display: -webkit-box; line-clamp: 2; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
              {{ route.desc }}
            </p>
            <!-- POI拖拽排序 -->
            <div style="margin-bottom: 15px;">
              <label style="font-size: 14px; font-weight: bold; margin-bottom: 8px; display: block;">POI顺序（拖拽排序）</label>
              <el-transfer
                v-model="route.poiIds"
                :data="poiTransferData"
                :titles="['可选POI', '已选POI']"
                :render-content="renderPoi"
                filterable
                @change="handleSortPoi(route.id)"
              />
            </div>
          </div>
        </div>
      </div>
    </el-card>
    <!-- 添加特色路线弹窗 -->
    <el-dialog v-model="showAddRouteDialog" title="添加特色路线" width="500px" @close="resetAddRouteForm">
      <el-form :model="addRouteForm" label-width="80px">
        <el-form-item label="路线名称" required>
          <el-input v-model="addRouteForm.name" placeholder="请输入特色路线名称" />
        </el-form-item>
        <el-form-item label="路线描述">
          <el-input v-model="addRouteForm.desc" type="textarea" rows="3" placeholder="请输入路线描述" />
        </el-form-item>
        <el-form-item label="关联POI" required>
          <el-transfer
            v-model="addRouteForm.poiIds"
            :data="poiTransferData"
            :titles="['可选POI', '已选POI']"
            :render-content="renderPoi"
            filterable
          />
        </el-form-item>
        <el-form-item label="封面图">
          <el-upload
            action="#"
            :show-file-list="false"
            :before-upload="handleBeforeUpload"
            style="width: 100%;"
          >
            <div v-if="addRouteForm.cover" style="height: 200px; background: #f5f7fa; border-radius: 4px; overflow: hidden;">
              <img :src="addRouteForm.cover" alt="封面预览" style="width: 100%; height: 100%; object-fit: cover;" />
            </div>
            <div v-else style="height: 200px; border: 1px dashed #dcdcdc; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #909399;">
              <el-icon size="40"><UploadFilled /></el-icon>
              <p style="margin-left: 10px;">点击上传封面图</p>
            </div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddRouteDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddRoute">确认添加</el-button>
      </template>
    </el-dialog>
    <!-- 封面上传弹窗（简化） -->
    <el-upload
      ref="uploadRef"
      action="#"
      :show-file-list="false"
      :before-upload="handleBeforeUpload"
      style="display: none;"
    ></el-upload>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, type VNode } from 'vue';
import { ElMessage, ElTransfer, type TransferDataItem } from 'element-plus';
import { Picture, UploadFilled } from '@element-plus/icons-vue';
import { useAdminStore } from '@/store';
import type { FeatureRoute } from '@/types/admin';
// 导入ElUpload及正确类型，合并导入避免重复
import { ElUpload, type UploadInstance } from 'element-plus';

const store = useAdminStore();
// 基础配置表单
const configForm = ref({
  slopeWeight: store.config.slopeWeight
});
// 添加路线弹窗
const showAddRouteDialog = ref(false);
// 添加路线表单
const addRouteForm = ref<Omit<FeatureRoute, 'id'>>({
  name: '',
  cover: '',
  poiIds: [],
  desc: ''
});
// ElUpload实例引用（正确类型）
const uploadRef = ref<UploadInstance | null>(null);
// 当前上传封面的路线ID
const currentCoverRouteId = ref(0);

// POI转换为穿梭框数据（严格匹配TransferDataItem官方类型）
const poiTransferData = computed<TransferDataItem[]>(() => {
  return store.poiList
    .filter(poi => poi.status)
    .map(poi => ({
      key: poi.id,
      label: `${poi.name}（${poi.type === 'entrance' ? '入口' : poi.type === 'view' ? '景点' : poi.type === 'rest' ? '休息区' : '出口'}）`
    }));
});

// 修复1-3：自定义渲染函数类型，显式约束参数+返回值，消除隐式any
type TransferRenderFn = (h: (tag: string, children: string) => VNode, option: TransferDataItem) => VNode;
const renderPoi: TransferRenderFn = (h, option) => {
  return h('span', option.label);
};

// 保存基础配置
const handleSaveBaseConfig = () => {
  if (configForm.value.slopeWeight < 0 || configForm.value.slopeWeight > 1) {
    return ElMessage.warning('坡度权重必须在0到1之间');
  }
  store.updateConfig({ slopeWeight: configForm.value.slopeWeight });
  ElMessage.success('基础配置保存成功');
};

// 处理POI排序
const handleSortPoi = (routeId: number) => {
  const route = store.config.featureRoutes.find(r => r.id === routeId);
  if (route) {
    store.sortFeatureRoutePoi(routeId, route.poiIds);
    ElMessage.success('POI顺序修改成功');
  }
};

// 上传封面前置处理（转为Base64，简化实现）
const handleBeforeUpload = (file: File) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    const base64 = e.target?.result as string;
    if (currentCoverRouteId.value) {
      // 更换已有路线封面
      const route = store.config.featureRoutes.find(r => r.id === currentCoverRouteId.value);
      if (route) route.cover = base64;
      store.updateConfig({ featureRoutes: [...store.config.featureRoutes] });
      currentCoverRouteId.value = 0;
    } else {
      // 新增路线封面
      addRouteForm.value.cover = base64;
    }
    ElMessage.success('封面上传成功');
  };
  reader.readAsDataURL(file);
  return false; // 阻止默认上传
};

// 修复4：ElUpload触发上传的正确方式，通过$el获取DOM节点点击
const handleUploadCover = (routeId: number) => {
  currentCoverRouteId.value = routeId;
  uploadRef.value?.$el.click();
};

// 重置添加路线表单
const resetAddRouteForm = () => {
  addRouteForm.value = { name: '', cover: '', poiIds: [], desc: '' };
  currentCoverRouteId.value = 0;
};

// 添加特色路线
const handleAddRoute = () => {
  if (!addRouteForm.value.name) return ElMessage.warning('请输入路线名称');
  if (addRouteForm.value.poiIds.length < 2) return ElMessage.warning('至少选择2个POI组成路线');
  store.addFeatureRoute(addRouteForm.value);
  showAddRouteDialog.value = false;
  resetAddRouteForm();
  ElMessage.success('特色路线添加成功');
};

// 监听配置变化，同步表单
watch(
  () => store.config.slopeWeight,
  (val) => {
    configForm.value.slopeWeight = val;
  },
  { immediate: true }
);
</script>

<style scoped>
.system-config {
  flex: 1;
}
</style>