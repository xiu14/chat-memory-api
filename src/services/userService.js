import { message } from 'antd';

const API_BASE_URL = 'http://localhost:3002';

// 获取用户宝石数据
export async function getUserGemData() {
  try {
    console.log('开始获取宝石数据...');
    const response = await fetch(`${API_BASE_URL}/api/gems/get`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error('获取数据失败');
    }
    
    const result = await response.json();
    console.log('服务器返回的原始数据:', result);
    
    if (!result) {
      console.log('暂无数据');
      return null;
    }
    
    // 解析存储的 JSON 数据
    const parsedData = result.data ? JSON.parse(result.data) : null;
    console.log('解析后的数据:', parsedData);
    return parsedData;
  } catch (error) {
    console.error('获取宝石数据失败:', error);
    return null;
  }
}

// 保存用户宝石数据
export async function saveUserGemData(userId, gemData) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/gems/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(gemData)
    });
    
    if (!response.ok) {
      throw new Error('保存数据失败');
    }
    
    const result = await response.json();
    if (result.success) {
      message.success('数据保存成功');
      return true;
    } else {
      throw new Error('保存失败');
    }
  } catch (error) {
    console.error('保存宝石数据失败:', error);
    message.error(error.message || '保存失败');
    return false;
  }
}

// 检查是否有历史数据
export async function checkGemDataExists() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/gems/check`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      return false;
    }
    
    const data = await response.json();
    return data.exists;
  } catch (error) {
    console.error('检查数据失败:', error);
    return false;
  }
}

// 添加测试数据函数
export async function addTestData() {
  const testData = {
    gems: [
      { 
        name: "测试宝石1",
        count: 10,
        price: 100
      },
      { 
        name: "测试宝石2",
        count: 5,
        price: 200
      }
    ],
    updateTime: new Date().toISOString()
  };

  return await saveUserGemData(null, testData);
} 