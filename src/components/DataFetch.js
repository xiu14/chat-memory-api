import { auth } from '../firebase';
import { message } from 'antd';
import { saveUserGemData } from '../services/userService';
import { useGem } from '../context/GemContext';
import { useState } from 'react';
import { Button, Form, Input, Card } from 'antd';

function DataFetch() {
  const { gemData, setGemData } = useGem();  // 获取 gemData
  const [websiteLoggedIn, setWebsiteLoggedIn] = useState(false);

  // 显示宝石数据的组件
  const GemDataDisplay = () => {
    if (!gemData) {
      return <p>暂无数据</p>;
    }

    return (
      <Card title="宝石数据">
        {/* 根据实际数据结构显示内容 */}
        <pre>{JSON.stringify(gemData, null, 2)}</pre>
      </Card>
    );
  };

  // 抓取新数据的部分
  const FetchNewData = () => {
    return (
      <Card title="抓取新数据">
        {!websiteLoggedIn ? (
          <div>
            <h3>需要登录网站才能抓取新数据</h3>
            <WebsiteLoginForm onLogin={loginToWebsite} />
          </div>
        ) : (
          <Button onClick={fetchGemData}>抓取最新数据</Button>
        )}
      </Card>
    );
  };

  // 网站登录状态检查
  const checkWebsiteLoginStatus = async () => {
    try {
      // 这里需要根据实际情况检查网站的登录状态
      // 比如检查某个特定的 cookie 或者发送请求到网站验证登录状态
      const isLoggedIn = await checkWebsiteLogin(); // 实现这个函数
      setWebsiteLoggedIn(isLoggedIn);
      return isLoggedIn;
    } catch (error) {
      console.error('检查网站登录状态失败:', error);
      return false;
    }
  };

  async function fetchGemData() {
    try {
      // 首先检查程序用户是否登录
      const currentUser = auth.currentUser;
      if (!currentUser) {
        throw new Error('请先登录程序');
      }

      // 然后检查网站是否登录
      const isWebsiteLoggedIn = await checkWebsiteLoginStatus();
      if (!isWebsiteLoggedIn) {
        throw new Error('请先登录网站');
      }

      // 开始抓取数据
      const gemData = await scrapeGemData();
      
      const saved = await saveUserGemData(currentUser.uid, gemData);
      if (!saved) {
        throw new Error('数据保存失败');
      }
      
      setGemData(gemData);
      message.success('数据抓取并保存成功！');
    } catch (error) {
      console.error('数据抓取失败:', error);
      message.error(error.message || '数据抓取失败，请重试');
    }
  }

  // 网站登录函数
  const loginToWebsite = async (websiteUsername, websitePassword) => {
    try {
      // 实现网站的登录逻辑
      const success = await performWebsiteLogin(websiteUsername, websitePassword);
      if (success) {
        setWebsiteLoggedIn(true);
        message.success('网站登录成功！');
      } else {
        throw new Error('网站登录失败');
      }
    } catch (error) {
      message.error('网站登录失败：' + error.message);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      {/* 显示现有数据 */}
      <GemDataDisplay />
      
      {/* 分隔线 */}
      <div style={{ margin: '20px 0' }} />
      
      {/* 抓取新数据的部分 */}
      <FetchNewData />
    </div>
  );
}

// 网站登录表单组件
function WebsiteLoginForm({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(username, password);
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Input
        placeholder="网站用户名"
        value={username}
        onChange={e => setUsername(e.target.value)}
      />
      <Input.Password
        placeholder="网站密码"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />
      <Button type="primary" htmlType="submit">
        登录网站
      </Button>
    </Form>
  );
}

export default DataFetch; 