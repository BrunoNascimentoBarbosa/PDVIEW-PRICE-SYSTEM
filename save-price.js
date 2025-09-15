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
const HOST = '0.0.0.0'; // Bind em todas as interfaces

server.listen(PORT, HOST, () => {
    console.log(`Servidor de preços rodando em ${HOST}:${PORT}`);
    console.log(`Use http://localhost:${PORT}/save-price para salvar preços`);
    console.log(`Use http://localhost:${PORT}/get-price para buscar preços`);

    // Obtém IP local
    const os = require('os');
    const networkInterfaces = os.networkInterfaces();
    Object.keys(networkInterfaces).forEach(interface => {
        networkInterfaces[interface].forEach(details => {
            if (details.family === 'IPv4' && !details.internal) {
                console.log(`Rede local: http://${details.address}:${PORT}`);
            }
        });
    });
});

// Tratamento de erros
server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
        console.error(`Erro: Porta ${PORT} já está em uso`);
        console.error('Verifique se outro processo está usando a porta');
        console.error('Use: lsof -i :3000 ou netstat -tulpn | grep 3000');
    } else if (error.code === 'EACCES') {
        console.error(`Erro: Sem permissão para usar a porta ${PORT}`);
        console.error('Tente executar com sudo ou use uma porta > 1024');
    } else {
        console.error('Erro no servidor:', error);
    }
    process.exit(1);
});