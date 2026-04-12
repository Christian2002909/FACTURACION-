const express = require('express');
const { generateXML } = require('facturacionelectronicapy-xmlgen');
const { signXML } = require('facturacionelectronicapy-xmlsign');
const { sendDE, cancelDE, consultDE } = require('facturacionelectronicapy-setapi');

const app = express();
app.use(express.json({ limit: '10mb' }));

// Solo aceptar conexiones locales
app.listen(3001, '127.0.0.1', () => {
  console.log('SIFEN service escuchando en localhost:3001');
});

// POST /generar-xml → recibe {params, data} → retorna {xml}
app.post('/generar-xml', async (req, res) => {
  try {
    const { params, data } = req.body;
    const xml = await generateXML(params, data);
    res.json({ xml });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// POST /firmar-xml → recibe {xml, certPath, certPassword} → retorna {xmlFirmado}
app.post('/firmar-xml', async (req, res) => {
  try {
    const { xml, certPath, certPassword } = req.body;
    const xmlFirmado = await signXML(xml, certPath, certPassword);
    res.json({ xmlFirmado });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// POST /enviar-sifen → recibe {xml, ambiente} → retorna {cdc, estado, protocolo, mensaje}
app.post('/enviar-sifen', async (req, res) => {
  try {
    const { xml, ambiente } = req.body;
    const resultado = await sendDE(xml, ambiente === 'prod' ? 'prod' : 'test');
    res.json(resultado);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// POST /cancelar → recibe {cdc, motivo, params, ambiente} → retorna resultado
app.post('/cancelar', async (req, res) => {
  try {
    const { cdc, motivo, params, ambiente } = req.body;
    const resultado = await cancelDE(cdc, motivo, params, ambiente === 'prod' ? 'prod' : 'test');
    res.json(resultado);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// POST /consultar → recibe {cdc, ambiente} → retorna estado actual en SIFEN
app.post('/consultar', async (req, res) => {
  try {
    const { cdc, ambiente } = req.body;
    const resultado = await consultDE(cdc, ambiente === 'prod' ? 'prod' : 'test');
    res.json(resultado);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});
