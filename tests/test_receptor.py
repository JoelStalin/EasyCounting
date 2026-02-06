from fastapi.testclient import TestClient
from app.main import app

def test_receive_arecf_valid():
    """
    Tests that the /receptor/arecf endpoint correctly handles a valid ARECF XML.
    """
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<ARECF>
    <DetalleAcusedeRecibo>
        <Version>1.0</Version>
        <RNCEmisor>10100000001</RNCEmisor>
        <RNCComprador>10100000002</RNCComprador>
        <eNCF>E310000000001</eNCF>
        <Estado>0</Estado>
        <FechaHoraAcuseRecibo>01-01-2024 12:00:00</FechaHoraAcuseRecibo>
    </DetalleAcusedeRecibo>
</ARECF>
"""
    with TestClient(app) as client:
        response = client.post("/receptor/arecf", content=xml_content)
    assert response.status_code == 202
    assert response.json() == {"status": "ARECF received, validated, and queued for processing"}

def test_receive_arecf_invalid():
    """
    Tests that the /receptor/arecf endpoint correctly handles an invalid ARECF XML.
    """
    xml_content = b"<invalid-xml/>"
    with TestClient(app) as client:
        response = client.post("/receptor/arecf", content=xml_content)
    assert response.status_code == 400
    assert response.text == "Invalid ARECF XML"

def test_receive_acecf_valid():
    """
    Tests that the /receptor/acecf endpoint correctly handles a valid ACECF XML.
    """
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<ACECF>
    <DetalleAprobacionComercial>
        <Version>1.0</Version>
        <RNCEmisor>10100000001</RNCEmisor>
        <eNCF>E310000000001</eNCF>
        <MontoTotal>1000.00</MontoTotal>
        <TotalITBIS>180.00</TotalITBIS>
        <FechaHoraAprobacion>01-01-2024 12:00:00</FechaHoraAprobacion>
        <DetalleItemsAprobados>
            <Item>
                <NumeroLinea>1</NumeroLinea>
                <CantidadAprobada>10</CantidadAprobada>
            </Item>
        </DetalleItemsAprobados>
    </DetalleAprobacionComercial>
</ACECF>
"""
    with TestClient(app) as client:
        response = client.post("/receptor/acecf", content=xml_content)
    assert response.status_code == 202
    assert response.json() == {"status": "ACECF received, validated, and queued for processing and submission to DGII"}

def test_receive_anecf_valid():
    """
    Tests that the /receptor/anecf endpoint correctly handles a valid ANECF XML.
    """
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<ANECF>
    <DetalleAnulacion>
        <Version>1.0</Version>
        <RNCEmisor>10100000001</RNCEmisor>
        <eNCF>E310000000001</eNCF>
        <MotivoAnulacion>Test</MotivoAnulacion>
        <FechaHoraAnulacion>01-01-2024 12:00:00</FechaHoraAnulacion>
    </DetalleAnulacion>
</ANECF>
"""
    with TestClient(app) as client:
        response = client.post("/receptor/anecf", content=xml_content)
    assert response.status_code == 202
    assert response.json() == {"status": "ANECF received, validated, and queued for processing"}
