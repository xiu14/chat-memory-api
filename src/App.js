import { useEffect } from 'react';
import { GemProvider } from './context/GemContext';
import { getUserGemData } from './services/userService';
import Login from './components/Login';
import DataFetch from './components/DataFetch';
import { message } from 'antd';
// 其他需要的导入...

function App() {
  const { setGemData } = useGem();

  useEffect(() => {
    // 程序启动时加载数据
    async function loadInitialData() {
      try {
        const data = await getUserGemData();
        if (data) {
          setGemData(data);
          message.success('已加载历史数据');
        }
      } catch (error) {
        console.error('加载历史数据失败:', error);
      }
    }

    loadInitialData();
  }, []);

  return (
    <GemProvider>
      <div className="App">
        <Login />
        <DataFetch />
        {/* 其他组件 */}
      </div>
    </GemProvider>
  );
}

export default App; 