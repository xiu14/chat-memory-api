const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
app.use(express.json());

// 连接到数据库
const db = new sqlite3.Database(path.join(process.env.USERPROFILE, 'users.db'), (err) => {
  if (err) {
    console.error('数据库连接失败:', err);
  } else {
    console.log('成功连接到数据库');
  }
});

// 获取宝石数据
app.get('/api/gems/get', (req, res) => {
  db.get('SELECT * FROM gems ORDER BY id DESC LIMIT 1', [], (err, row) => {
    if (err) {
      console.error('获取数据失败:', err);
      res.status(500).json({ error: '获取数据失败' });
      return;
    }
    res.json(row || null);
  });
});

// 保存宝石数据
app.post('/api/gems/save', (req, res) => {
  const gemData = req.body;
  db.run('INSERT INTO gems (data, created_at) VALUES (?, datetime("now"))', 
    [JSON.stringify(gemData)], 
    function(err) {
      if (err) {
        console.error('保存数据失败:', err);
        res.status(500).json({ error: '保存数据失败' });
        return;
      }
      res.json({ success: true, id: this.lastID });
    });
});

// 检查是否有数据
app.get('/api/gems/check', (req, res) => {
  db.get('SELECT COUNT(*) as count FROM gems', [], (err, row) => {
    if (err) {
      console.error('检查数据失败:', err);
      res.status(500).json({ error: '检查数据失败' });
      return;
    }
    res.json({ exists: row.count > 0 });
  });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
}); 