import type { PathSamplingPoint } from './index';

// 高程剖面图表Props类型
export interface ElevationProfileProps {
  data: PathSamplingPoint[]; // 采样点数据（必传）
  width?: string;            // 图表宽度（可选，默认100%）
  height?: string;           // 图表高度（可选，默认300px）
  title?: string;            // 图表标题（可选）
  elevationColor?: string;   // 高程系列颜色（可选）
  slopeColor?: string;       // 坡度系列颜色（可选）
}