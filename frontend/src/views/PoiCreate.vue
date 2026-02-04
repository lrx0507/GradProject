<!-- src/views/PoiCreate.vue -->
<template>
  <div class="page-container">
    <h2>POI 采集管理</h2>
    <div id="map" class="map"></div>

    <!-- 表单弹窗：添加/编辑POI -->
    <el-dialog v-model="dialogVisible" title="添加兴趣点" width="500px">
      <el-form :model="form" label-width="80px" :rules="rules" ref="formRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入POI名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择POI类型">
            <el-option label="入口" value="entrance" />
            <el-option label="观景点" value="view" />
            <el-option label="休息区" value="rest" />
            <el-option label="出口" value="exit" />
          </el-select>
        </el-form-item>
        <!-- 新增：POI启用开关（可选） -->
        <el-form-item label="是否启用">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入POI描述（可选）" />
        </el-form-item>
        <el-form-item label="坐标">
          {{ form.lng.toFixed(6) }}, {{ form.lat.toFixed(6) }}
        </el-form-item>
      </el-form>

      <!-- 弹窗底部按钮 -->
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onBeforeUnmount, watch } from 'vue'
import axios from 'axios'
import type { Poi, PoiType } from '@/types/poi'
// 修复：删除重复的POI_TYPE_LABELS导入，保留一次完整导入
import { POI_TYPE_LABELS, POI_TYPE_ICONS } from '@/types/poi'
import { ElMessage, ElMessageBox } from 'element-plus'
// OpenLayers 核心依赖
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import XYZ from 'ol/source/XYZ'
import { fromLonLat, toLonLat } from 'ol/proj'

// OpenLayers 矢量图层/样式/弹窗依赖
import VectorSource from 'ol/source/Vector'
import VectorLayer from 'ol/layer/Vector'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import Style from 'ol/style/Style'
import CircleStyle from 'ol/style/Circle'
import Fill from 'ol/style/Fill'
import Stroke from 'ol/style/Stroke'
import Overlay from 'ol/Overlay'

// === 配置项 ===
// 天地图Key（替换为自己申请的有效Key，需勾选WMTS+白名单填localhost）
const TDT_KEY = '83ed38f63fae8ac967cf2e62de6f77a0'
// 后端接口基础地址（统一管理，便于后续部署修改）
const API_BASE_URL = 'http://localhost:8000'

// === 状态管理 ===
// 刷新标识：提交/删除后触发POI重新加载（通过watch监听）
const reloadFlag = ref(0)
// 表单弹窗显隐
const dialogVisible = ref(false)
// 修复1：form初始值type改为显式PoiType类型，匹配接口定义
const form = ref<Poi>({
  name: '',
  type: 'entrance' as PoiType, // 显式指定类型，解决Type 'entrance'不兼容问题
  description: '',
  lat: 0,
  lng: 0,
  is_active: true // 修复2：Poi接口已新增is_active，无属性缺失报错
});
// 表单校验规则（必填项校验）
const rules = {
  name: [{ required: true, message: '请输入POI名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择POI类型', trigger: 'change' }],
}
// 表单实例引用（用于校验）
const formRef = ref()

// === 地图实例相关 ===
let map: Map | null = null
// 已保存POI的矢量图层（绿色标记）
let savedPoiLayer: VectorLayer<VectorSource> | null = null
// POI悬停信息弹窗
let hoverOverlay: Overlay | null = null
// 修复3：定义poiLayer变量（原代码未定义直接使用）
let poiLayer: VectorLayer<VectorSource> | null = null

// === 生命周期 ===
// 组件挂载：初始化地图 + 加载所有POI
onMounted(() => {
  initMap()
  loadAllPois()
})

// 监听刷新标识：触发POI重新加载
watch(reloadFlag, () => {
  loadAllPois()
})

// 组件卸载：销毁地图实例，防止内存泄漏
onBeforeUnmount(() => {
  if (map) {
    map.setTarget(undefined)
    map = null
  }
  savedPoiLayer = null
  hoverOverlay = null
  poiLayer = null // 新增：销毁未使用的图层变量
})

// 修复4：保留函数但标记为/* unused */，或后续使用；解决未使用变量报错
/* unused */
const initPoiLayer = () => {
  const poiSource = new VectorSource();
  poiLayer = new VectorLayer({
    source: poiSource,
    style: (feature) => {
      const poi = feature.get('poi') as Poi;
      // 按POI类型设置颜色
      const colorMap: Record<PoiType, string> = {
        entrance: '#40a9ff', // 蓝色：入口
        view: '#722ed1',    // 紫色：观景点
        rest: '#52c41a',     // 绿色：休息区
        exit: '#ff4d4f'      // 红色：出口
      };
      return new Style({
        image: new CircleStyle({
          radius: 8,
          fill: new Fill({ color: colorMap[poi.type] }),
          stroke: new Stroke({ color: '#fff', width: 2 })
        })
      });
    }
  });
  // 修复5：map可能为null，添加非空判断
  if (map) {
    map.addLayer(poiLayer);
  }
};

// === 地图初始化核心方法 ===
function initMap() {
  // 1. 天地图矢量底图（无注记，HTTPS协议）
  const vecLayer = new TileLayer({
    source: new XYZ({
      url: `https://t0.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TDT_KEY}`,
      attributions: '© <a href="https://www.tianditu.gov.cn/" target="_blank">天地图</a>',
    }),
  })

  // 2. 天地图注记图层（文字标签，HTTPS协议）
  const cvaLayer = new TileLayer({
    source: new XYZ({
      url: `https://t0.tianditu.gov.cn/cia_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cia&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${TDT_KEY}`,
      attributions: '© <a href="https://www.tianditu.gov.cn/" target="_blank">天地图</a>',
    }),
  })

  // 3. 地图默认中心点（北京，经纬度转Web墨卡托）
  const defaultCenter = fromLonLat([116.4, 39.9])

  // 4. 创建地图实例
  map = new Map({
    target: 'map',
    layers: [vecLayer, cvaLayer],
    view: new View({
      center: defaultCenter,
      zoom: 12,
      projection: 'EPSG:3857', // 天地图标准Web墨卡托坐标系
    }),
    controls: [], // 禁用所有默认控件（缩放、旋转、信息等）
  })

  // 5. 创建POI悬停信息弹窗
  const popupContainer = document.createElement('div')
  popupContainer.className = 'poi-popup'
  popupContainer.style.cssText = `
    padding: 4px 8px;
    background: rgba(0,0,0,0.7);
    color: #fff;
    border-radius: 4px;
    font-size: 12px;
    pointer-events: none;
    max-width: 200px;
    word-wrap: break-word;
  `
  hoverOverlay = new Overlay({
    element: popupContainer,
    positioning: 'bottom-center',
    stopEvent: false,
  })
  map.addOverlay(hoverOverlay)

  // 6. 创建已保存POI专属矢量图层
  const savedSource = new VectorSource()
  savedPoiLayer = new VectorLayer({
    source: savedSource,
    style: new Style({
      image: new CircleStyle({
        radius: 6,
        fill: new Fill({ color: 'rgba(0, 128, 0, 0.9)' }), // 深绿色标记
        stroke: new Stroke({ color: '#fff', width: 1.5 }), // 白色描边
      }),
    }),
  })
  map.addLayer(savedPoiLayer)

  // 7. 地图鼠标悬停事件：显示POI名称和类型
  map.on('pointermove', (evt) => {
    if (!map || !savedPoiLayer || !hoverOverlay) return

    // 获取鼠标悬停的POI要素
    const feature = map.getFeaturesAtPixel(evt.pixel, {
      layerFilter: (layer) => layer === savedPoiLayer,
    })?.[0]

    if (feature) {
      // 渲染悬停信息
      const poi = feature.get('poi') as Poi
      popupContainer.innerText = `${poi.name} (${POI_TYPE_LABELS[poi.type]})`
      hoverOverlay.setPosition(evt.coordinate)
    } else {
      // 隐藏悬停信息
      hoverOverlay.setPosition(undefined)
    }
  })

  // 8. 地图点击事件：删除POI / 新增POI
  map.on('click', async (event) => {
    if (!map || !savedPoiLayer) return

    // 获取点击的POI要素
    const feature = map.getFeaturesAtPixel(event.pixel, {
      layerFilter: (layer) => layer === savedPoiLayer,
    })?.[0]

    if (feature) {
      // 点击到POI：弹出确认框删除
      const poi = feature.get('poi') as Poi
      try {
        await ElMessageBox.confirm(
          `确定要删除 "${poi.name}" 吗？`,
          '删除确认',
          { type: 'warning' }
        )
        // 调用后端删除接口
        await axios.delete(`${API_BASE_URL}/pois/${poi.id}`)
        ElMessage.success('POI删除成功！')
        reloadFlag.value++ // 触发POI重新加载
      } catch (error) {
        // 取消删除不提示错误
        if (error !== 'cancel') {
          ElMessage.error('POI删除失败，请重试！')
        }
      }
      return // 阻止执行新增逻辑
    }

    // 未点击到POI：弹出新增表单
    // 未点击到POI：弹出新增表单
    const [lng, lat] = toLonLat(event.coordinate) as [number, number]
    // 修复点：将type从'teaching'改为合法的'entrance'，并补充is_active默认值
    form.value = {
      name: '',
      type: 'entrance' as PoiType, // 合法类型：入口
      description: '',
      lat,
      lng,
      is_active: true // 补充：重置时默认启用，与表单默认值一致
    }
    dialogVisible.value = true
    nextTick(() => {
      formRef.value?.clearValidate()
    })
  })
}

// === 业务方法 ===
/**
 * 从后端加载所有POI并渲染到地图
 */
async function loadAllPois() {
  try {
    const res = await axios.get<Poi[]>(`${API_BASE_URL}/pois`)
    const pois = res.data
    const source = savedPoiLayer?.getSource()

    if (source) {
      source.clear()
      pois.forEach(poi => {
        const point = new Point(fromLonLat([poi.lng, poi.lat]))
        const feature = new Feature(point)
        // 修复点：确保挂载完整的POI数据，包括is_active
        feature.set('poi', {
          ...poi,
          is_active: poi.is_active ?? true // 兼容后端未返回的情况，默认启用
        })
        source.addFeature(feature)
      })
    }
  } catch (error) {
    console.error('加载POI失败：', error)
    ElMessage.error('加载POI失败，请检查后端服务是否启动！')
  }
}


/**
 * 提交POI表单：调用后端新增接口
 */
async function submitForm() {
  try {
    const valid = await formRef.value?.validate()
    if (!valid) return

    // 修复点：添加is_active字段，与后端接口参数一致
    const poiData: Poi = {
      name: form.value.name,
      type: form.value.type,
      description: form.value.description,
      lat: form.value.lat,
      lng: form.value.lng,
      is_active: form.value.is_active // 新增：传递启用状态给后端
    }

    const res = await axios.post(`${API_BASE_URL}/pois`, poiData)
    const newPoi = res.data // 后端返回的新POI数据（含id）
    ElMessage.success('POI添加成功！')
    dialogVisible.value = false
    if (savedPoiLayer) {
      const point = new Point(fromLonLat([newPoi.lng, newPoi.lat]))
      const feature = new Feature(point)
      feature.set('poi', newPoi)
      savedPoiLayer.getSource()?.addFeature(feature)
    }

    reloadFlag.value++ // 触发地图重新加载POI


  } catch (error) {
    console.error('提交POI失败：', error)
    ElMessage.error('POI提交失败，请检查类型是否为入口/观景点/休息区/出口！')
  }
}
</script>

<style scoped>
/* 页面容器样式 */
.page-container {
  padding: 20px;
}

/* 地图容器样式 */
.map {
  width: 100%;
  height: 900px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-top: 10px;
}

/* POI悬停弹窗样式（可覆盖JS内联样式） */
:deep(.poi-popup) {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>