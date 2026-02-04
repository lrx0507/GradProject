// src/types/modules.d.ts - 全局第三方模块类型声明（无any，符合ESLint规范）
declare module 'gpxparser' {
  // 极简基础类型定义，满足ESLint no-explicit-any规则
  class GPXParser {
    // 仅声明构造函数，匹配实际使用方式（new GPXParser()）
    constructor();
    // 可选：声明常用方法，提升类型提示（无实际使用可省略）
    parse?(gpxString: string): void;
    tracks?: Array<{
      name?: string;
      segments?: Array<{
        points?: Array<{
          lat: number;
          lon: number;
          ele?: number;
        }>;
      }>;
    }>;
  }
  export default GPXParser;
}