const fs = require('fs');
const path = require('path');
const http = require('http');

const server = http.createServer((req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // GET endpoint para buscar preços
    if (req.method === 'GET' && req.url === '/get-price') {
        const filePath = path.join(__dirname, 'price', 'current-price.json');
        
        if (fs.existsSync(filePath)) {
            const data = fs.readFileSync(filePath, 'utf8');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(data);
        } else {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, message: 'Arquivo de preços não encontrado' }));
        }
        return;
    }

    // POST endpoint para salvar preços
    if (req.method === 'POST' && req.url === '/save-price') {
        let body = '';
        
        req.on('data', chunk => {
            body += chunk.toString();
        });
        
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                
                if (data.etanol && data.gasolina) {
                    const priceData = {
                        etanol: parseFloat(data.etanol),
                        gasolina: parseFloat(data.gasolina),
                        timestamp: new Date().toISOString()
                    };
                    
                    // Criar pasta price se não existir
                    const priceDir = path.join(__dirname, 'price');
                    if (!fs.existsSync(priceDir)) {
                        fs.mkdirSync(priceDir);
                    }
                    
                    // Salvar arquivo JSON
                    const filePath = path.join(priceDir, 'current-price.json');
                    fs.writeFileSync(filePath, JSON.stringify(priceData, null, 2));
                    
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: true, message: 'Preços salvos com sucesso' }));
                } else {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: false, message: 'Dados inválidos' }));
                }
            } catch (error) {
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, message: 'Erro ao processar dados' }));
            }
        });
    } else {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, message: 'Rota não encontrada' }));
    }
});

const PORT = 3000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`Servidor de preços rodando na porta ${PORT}`);
    console.log(`Use http://localhost:${PORT}/save-price para salvar preços`);
    console.log(`Use http://localhost:${PORT}/get-price para buscar preços`);
    console.log(`Ou http://192.168.15.9:${PORT} da rede local`);
});