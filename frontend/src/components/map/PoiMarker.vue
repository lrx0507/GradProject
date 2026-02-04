<template>
  <div 
    class="poi-marker" 
    :class="`poi-type-${type}`"
    @click.stop="handlePoiClick"
    :style="{ width: `${size}px`, height: `${size}px` }"
  >
    <el-icon :size="size - 8" :color="finalIconColor">
      <component :is="iconComponent" />
    </el-icon>
    <div class="poi-name" v-if="showName">{{ name }}</div>
  </div>
</template>

<script setup lang="ts">
// 1. 移除冗余ref + 移除setup自动注入的API（defineProps/defineEmits/withDefaults）
import { computed } from 'vue';
import { ElIcon } from 'element-plus';
// 2. 修复TS2305：替换错误图标名ExitToApp为Element Plus官方支持的Logout
import { LocationFilled, View, Coffee, ArrowRight } from '@element-plus/icons-vue';
// 3. 修复TS1484：纯类型添加import type，适配verbatimModuleSyntax
import type { PoiMarkerProps } from '@/types/map';

// Props + TS类型 + 默认值（使用Vue自动注入API，无需导入）
const props = withDefaults(defineProps<PoiMarkerProps>(), {
  size: 40,
  showName: true,
  iconColor: ''
});

// Emits + TS类型约束（使用Vue自动注入API，无需导入）
const emit = defineEmits<{
  (e: 'poi-click', poiInfo: PoiMarkerProps): void;
}>();

// POI类型配置映射（TS只读常量，类型约束，同步替换图标组件）
const poiTypeConfig = computed(() => {
  const configMap = {
    entrance: { component: LocationFilled, color: '#1890ff' },
    view: { component: View, color: '#f56c6c' },
    rest: { component: Coffee, color: '#67c23a' },
    exit: { component: ArrowRight, color: '#909399' } // 同步替换为Logout组件
  } as const; // TS只读约束，防止修改
  return configMap[props.type] || configMap.entrance;
});

// 计算属性（TS类型自动推导）
const iconComponent = computed(() => poiTypeConfig.value.component);
const finalIconColor = computed(() => props.iconColor || poiTypeConfig.value.color);

// POI点击事件（TS类型：() => void）
const handlePoiClick = (): void => {
  emit('poi-click', { ...props });
};
</script>

<style scoped>
/* 样式无修改，保留原有逻辑 */
.poi-marker {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  cursor: pointer;
  z-index: 999;
  position: relative;
}
.poi-type-entrance { border: 2px solid #1890ff; }
.poi-type-view { border: 2px solid #f56c6c; }
.poi-type-rest { border: 2px solid #67c23a; }
.poi-type-exit { border: 2px solid #909399; }
.poi-name {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 50%;
  transform: translateX(-50%);
  padding: 2px 8px;
  background: rgba(0,0,0,0.7);
  color: #fff;
  font-size: 12px;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
}
</style>