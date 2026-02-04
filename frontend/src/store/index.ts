// src/store/index.ts
import { defineStore } from 'pinia';
import type { PoiInfo, RoadEdge, TopoNode, SystemConfig, OperationLog, StatData } from '@/types/admin';
import { ElMessage } from 'element-plus';

// 模拟初始数据（后续可替换为接口请求）
const initPoiList: PoiInfo[] = [
  { id: 1, name: '主入口', type: 'entrance', lng: 116.40, lat: 39.90, desc: '景区主入口，可停车', status: true, createTime: '2026-02-04 10:00:00' },
  { id: 2, name: '观景台', type: 'view', lng: 116.41, lat: 39.91, desc: '俯瞰全景，视野极佳', status: true, createTime: '2026-02-04 10:30:00' }
];
const initRoadEdges: RoadEdge[] = [];
const initTopoNodes: TopoNode[] = [];
const initConfig: SystemConfig = {
  slopeWeight: 0.3,
  featureRoutes: [{ id: 1, name: '经典徒步路线', cover: '', poiIds: [1,2], desc: '主入口→观景台' }]
};
const initLogs: OperationLog[] = [
  { id: 1, operator: '管理员', type: 'add', content: '添加POI【观景台】', time: '2026-02-04 10:30:00' }
];

export const useAdminStore = defineStore('admin', {
  state: () => ({
    poiList: initPoiList, // POI列表
    roadEdges: initRoadEdges, // 路网边列表
    topoNodes: initTopoNodes, // 拓扑节点列表
    config: initConfig, // 系统配置
    logs: initLogs, // 操作日志
    currentPoi: null as PoiInfo | null, // 当前编辑POI
    currentRoad: null as RoadEdge | null // 当前编辑路网边
  }),
  getters: {
    // 统计数据
    statData: (state): StatData => {
      const poiCount = { entrance: 0, view: 0, rest: 0, exit: 0 };
      state.poiList.forEach(poi => poiCount[poi.type]++);
      return {
        poiCount,
        roadTotalLength: state.roadEdges.reduce((sum, road) => sum + road.length, 0),
        poiTotal: state.poiList.length,
        roadTotal: state.roadEdges.length,
        recentLogs: state.logs.slice(-10).reverse() // 最近10条日志
      };
    },
    // 孤立POI（未关联任何路网边）
    isolatedPoi: (state) => {
      // 提取所有路网边的点，匹配POI坐标（简化逻辑，后续可优化）
      const roadPoints = new Set<string>();
      state.roadEdges.forEach(road => {
        road.points.forEach(p => roadPoints.add(`${p.lng},${p.lat}`));
      });
      return state.poiList.filter(poi => !roadPoints.has(`${poi.lng},${poi.lat}`) && poi.status);
    }
  },
  actions: {
    // POI操作
    addPoi(poi: Omit<PoiInfo, 'id' | 'createTime'>) {
      const newPoi = {
        ...poi,
        id: Date.now(),
        createTime: new Date().toLocaleString()
      };
      this.poiList.push(newPoi);
      this.addLog(`添加POI【${poi.name}】`);
      ElMessage.success('POI添加成功');
    },
    editPoi(poi: PoiInfo) {
      const index = this.poiList.findIndex(p => p.id === poi.id);
      if (index > -1) {
        this.poiList[index] = poi;
        this.addLog(`编辑POI【${poi.name}】`);
        ElMessage.success('POI编辑成功');
      }
    },
    togglePoiStatus(id: number) {
      const poi = this.poiList.find(p => p.id === id);
      if (poi) {
        poi.status = !poi.status;
        this.addLog(`${poi.status ? '启用' : '禁用'}POI【${poi.name}】`);
        ElMessage.success(`POI${poi.status ? '启用' : '禁用'}成功`);
      }
    },
    // 路网操作
    addRoadEdge(road: Omit<RoadEdge, 'id' | 'length' | 'createTime'>) {
      // 计算折线长度（简化球面距离公式，单位：米）
      const calcLength = (points: typeof road.points) => {
        let len = 0;
        // 过滤无效点，确保数组无undefined
        const validPoints = points.filter((p): p is Exclude<typeof p, undefined> => !!p);
        if (validPoints.length < 2) return 0; // 单一点无长度
        
        for (let i = 1; i < validPoints.length; i++) {
          // 核心修复：非空断言! 告知TS元素绝对非空，消除编译器误报
          const prevPoint = validPoints[i-1]!;
          const currPoint = validPoints[i]!;
          const [lng1, lat1] = [prevPoint.lng, prevPoint.lat];
          const [lng2, lat2] = [currPoint.lng, currPoint.lat];
          
          const radLat1 = (lat1 * Math.PI) / 180;
          const radLat2 = (lat2 * Math.PI) / 180;
          const a = radLat1 - radLat2;
          const b = (lng1 * Math.PI) / 180 - (lng2 * Math.PI) / 180;
          let s = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin(a/2),2) + Math.cos(radLat1)*Math.cos(radLat2)*Math.pow(Math.sin(b/2),2)));
          s = s * 6378137; // 地球半径，单位：米
          len += Math.round(s * 10000) / 10000;
        }
        return len;
      };
      
      const newRoad = {
        ...road,
        id: Date.now(),
        length: calcLength(road.points),
        createTime: new Date().toLocaleString()
      };
      this.roadEdges.push(newRoad);
      this.addLog(`添加路网边（长度：${newRoad.length.toFixed(2)}米）`);
      ElMessage.success('路网边添加成功');
    },
    // 生成拓扑节点
    generateTopoNodes() {
      const nodeMap = new Map<string, TopoNode>();
      this.roadEdges.forEach(road => {
        const validPoints = road.points.filter((p): p is Exclude<typeof p, undefined> => !!p);
        validPoints.forEach(point => {
          const key = `${point.lng},${point.lat}`;
          if (!nodeMap.has(key)) {
            nodeMap.set(key, { id: Date.now() + Math.random(), lng: point.lng, lat: point.lat, connectEdges: [road.id] });
          } else {
            const node = nodeMap.get(key)!;
            if (!node.connectEdges.includes(road.id)) node.connectEdges.push(road.id);
          }
        });
      });
      this.topoNodes = Array.from(nodeMap.values());
      this.addLog(`生成拓扑节点，共${this.topoNodes.length}个`);
      ElMessage.success(`成功生成${this.topoNodes.length}个拓扑节点`);
    },
    // 系统配置操作
    updateConfig(config: Partial<SystemConfig>) {
      this.config = { ...this.config, ...config };
      this.addLog('修改系统配置参数');
      ElMessage.success('系统配置更新成功');
    },
    // 添加特色路线
    addFeatureRoute(route: Omit<import('@/types/admin').FeatureRoute, 'id'>) {
      const newRoute = { ...route, id: Date.now() };
      this.config.featureRoutes.push(newRoute);
      this.addLog(`添加特色路线【${route.name}】`);
      ElMessage.success('特色路线添加成功');
    },
    // 编辑特色路线POI排序
    sortFeatureRoutePoi(routeId: number, poiIds: number[]) {
      const route = this.config.featureRoutes.find(r => r.id === routeId);
      if (route) {
        route.poiIds = poiIds;
        this.addLog(`调整特色路线【${route.name}】POI排序`);
        ElMessage.success('POI排序更新成功');
      }
    },
    // 添加操作日志
    addLog(content: string) {
      const newLog: OperationLog = {
        id: Date.now(),
        operator: '管理员',
        type: 'add',
        content,
        time: new Date().toLocaleString()
      };
      this.logs.push(newLog);
    }
  }
});