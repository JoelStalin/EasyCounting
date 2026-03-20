#!/usr/bin/env python3
"""
Check DGII Certification Status
Revisa el estado actual de certificación en DGII
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.dgii_scraper.certification_bot import DGIICertificationBot


async def main():
    """Check certification status"""
    bot = DGIICertificationBot(rnc='25500706423', password='test')
    status = await bot.check_certification_status()
    
    print('╔══════════════════════════════════════════════════════════════╗')
    print('║          ESTADO DE CERTIFICACIÓN DGII - e-CF                  ║')
    print('╚══════════════════════════════════════════════════════════════╝')
    print()
    print(f'  RNC:                {status.get("rnc")}')
    print(f'  Estado Actual:      {status.get("certification_state")}')
    print(f'  Paso:               {status.get("step")}/15')
    print(f'  Mensaje:            {status.get("message")}')
    print()
    print('═' * 64)
    
    return status


if __name__ == '__main__':
    asyncio.run(main())
