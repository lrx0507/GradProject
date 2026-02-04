// src/api/system.ts
import axios from 'axios';

/**
 * 读取系统配置（如坡度权重α）
 */
export const getSystemConfig = async (key: string) => {
  const res = await axios.get(`http://localhost:8000/system-config/${key}`);
  return res.data;
};

/**
 * 修改系统配置（如调整坡度权重α）
 */
export const updateSystemConfig = async (key: string, new_value: string) => {
  const res = await axios.put(`http://localhost:8000/system-config/${key}`, {}, {
    params: { new_value }
  });
  return res.data;
};