const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const cors = require('cors');

const app = express();

// 配置CORS
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173'], // 允许的前端域名
  credentials: true, // 允许携带凭证
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], // 允许的HTTP方法
  allowedHeaders: ['Content-Type', 'Authorization'] // 允许的请求头
}));

app.use(express.json());

// 连接到数据库
const db = new sqlite3.Database(path.join(process.env.USERPROFILE, 'users.db'), (err) => {
  if (err) {
    console.error('数据库连接失败:', err);
  } else {
    console.log('成功连接到数据库');
    // 创建表
    db.run(`CREATE TABLE IF NOT EXISTS gems (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      data TEXT NOT NULL,
      created_at DATETIME NOT NULL
    )`, (err) => {
      if (err) {
        console.error('创建表失败:', err);
      } else {
        console.log('数据库表已准备就绪');
      }
    });
  }
});

// 获取宝石数据
app.get('/api/gems/get', (req, res) => {
  console.log('收到获取宝石数据请求');
  db.get('SELECT * FROM gems ORDER BY id DESC LIMIT 1', [], (err, row) => {
    if (err) {
      console.error('获取数据失败:', err);
      res.status(500).json({ error: '获取数据失败: ' + err.message });
      return;
    }
    console.log('查询结果:', row);
    res.json(row || null);
  });
});

// 保存宝石数据
app.post('/api/gems/save', (req, res) => {
  console.log('收到保存宝石数据请求:', req.body);
  const gemData = req.body;
  
  if (!gemData) {
    console.error('请求体为空');
    res.status(400).json({ error: '请求体不能为空' });
    return;
  }
  
  try {
    // 验证数据是否为有效的JSON
    JSON.stringify(gemData);
  } catch (err) {
    console.error('无效的JSON数据:', err);
    res.status(400).json({ error: '无效的JSON数据' });
    return;
  }
  
  db.run('INSERT INTO gems (data, created_at) VALUES (?, datetime("now"))', 
    [JSON.stringify(gemData)], 
    function(err) {
      if (err) {
        console.error('保存数据失败:', err);
        res.status(500).json({ error: '保存数据失败: ' + err.message });
        return;
      }
      console.log('数据保存成功，ID:', this.lastID);
      res.json({ success: true, id: this.lastID });
    });
});

// 检查是否有数据
app.get('/api/gems/check', (req, res) => {
  console.log('收到检查数据请求');
  db.get('SELECT COUNT(*) as count FROM gems', [], (err, row) => {
    if (err) {
      console.error('检查数据失败:', err);
      res.status(500).json({ error: '检查数据失败: ' + err.message });
      return;
    }
    console.log('数据检查结果:', row);
    res.json({ exists: row.count > 0 });
  });
});

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
}); 