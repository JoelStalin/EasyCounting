from __future__ import annotations

from decimal import Decimal
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.infra.settings import settings
from app.models.accounting import InvoiceLedgerEntry, TenantSettings
from app.models.billing import Plan, UsageRecord
from app.models.invoice import Invoice
from app.models.partner import PartnerAccount, PartnerTenantAssignment
from app.models.tenant import Tenant
from app.models.user import User
from app.shared.database import session_scope
from app.shared.security import hash_password


def _ensure_plan(
    name: str,
    *,
    precio_mensual: Decimal,
    precio_por_documento: Decimal,
    documentos_incluidos: int,
    max_facturas_mes: int,
    max_facturas_por_receptor_mes: int,
    max_monto_por_factura: Decimal,
    includes_recurring_invoices: bool,
    descripcion: str,
) -> Plan:
    with session_scope() as session:
        plan = session.scalar(select(Plan).where(Plan.name == name))
        if plan:
            plan.precio_mensual = precio_mensual
            plan.precio_por_documento = precio_por_documento
            plan.documentos_incluidos = documentos_incluidos
            plan.max_facturas_mes = max_facturas_mes
            plan.max_facturas_por_receptor_mes = max_facturas_por_receptor_mes
            plan.max_monto_por_factura = max_monto_por_factura
            plan.includes_recurring_invoices = includes_recurring_invoices
            plan.descripcion = descripcion
            session.flush()
            return plan
        plan = Plan(
            name=name,
            precio_mensual=precio_mensual,
            precio_por_documento=precio_por_documento,
            documentos_incluidos=documentos_incluidos,
            max_facturas_mes=max_facturas_mes,
            max_facturas_por_receptor_mes=max_facturas_por_receptor_mes,
            max_monto_por_factura=max_monto_por_factura,
            includes_recurring_invoices=includes_recurring_invoices,
            descripcion=descripcion,
        )
        session.add(plan)
        session.flush()
        return plan


def _ensure_tenant(
    *,
    name: str,
    rnc: str,
    env: str,
    dgii_base_ecf: str,
    dgii_base_fc: str,
    plan_id: int | None = None,
) -> Tenant:
    with session_scope() as session:
        tenant = session.scalar(select(Tenant).where(Tenant.rnc == rnc))
        if tenant:
            tenant.name = name
            tenant.env = env
            tenant.dgii_base_ecf = dgii_base_ecf
            tenant.dgii_base_fc = dgii_base_fc
            tenant.plan_id = plan_id
            session.flush()
            return tenant
        tenant = Tenant(
            name=name,
            rnc=rnc,
            env=env,
            plan_id=plan_id,
            dgii_base_ecf=dgii_base_ecf,
            dgii_base_fc=dgii_base_fc,
        )
        session.add(tenant)
        session.flush()
        return tenant


def _ensure_partner_account(*, name: str, slug: str, status: str = "activo") -> PartnerAccount:
    with session_scope() as session:
        account = session.scalar(select(PartnerAccount).where(PartnerAccount.slug == slug))
        if account:
            account.name = name
            account.status = status
            session.flush()
            return account
        account = PartnerAccount(name=name, slug=slug, status=status)
        session.add(account)
        session.flush()
        return account


def _ensure_assignment(*, partner_account_id: int, tenant_id: int, can_emit: bool, can_manage: bool) -> None:
    with session_scope() as session:
        assignment = session.scalar(
            select(PartnerTenantAssignment).where(
                PartnerTenantAssignment.partner_account_id == partner_account_id,
                PartnerTenantAssignment.tenant_id == tenant_id,
            )
        )
        if assignment:
            assignment.can_emit = can_emit
            assignment.can_manage = can_manage
            session.flush()
            return
        session.add(
            PartnerTenantAssignment(
                partner_account_id=partner_account_id,
                tenant_id=tenant_id,
                can_emit=can_emit,
                can_manage=can_manage,
            )
        )


def _ensure_user(
    *,
    email: str,
    password: str,
    role: str,
    phone: str,
    tenant_id: int,
    partner_account_id: int | None = None,
) -> User:
    with session_scope() as session:
        user = session.scalar(select(User).where(User.email == email))
        password_hash = hash_password(password)
        if user:
            user.tenant_id = tenant_id
            user.partner_account_id = partner_account_id
            user.role = role
            user.phone = phone
            user.password_hash = password_hash
            user.status = "activo"
            if not user.mfa_secret:
                user.mfa_secret = ""
            session.flush()
            return user
        user = User(
            tenant_id=tenant_id,
            partner_account_id=partner_account_id,
            email=email,
            phone=phone,
            password_hash=password_hash,
            mfa_secret="",
            role=role,
            status="activo",
        )
        session.add(user)
        session.flush()
        return user


def _ensure_tenant_settings(tenant_id: int) -> None:
    with session_scope() as session:
        tenant_settings = session.scalar(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
        if tenant_settings:
            tenant_settings.moneda = "DOP"
            tenant_settings.correo_facturacion = tenant_settings.correo_facturacion or "facturacion@demo.getupsoft.com.do"
            tenant_settings.telefono_contacto = tenant_settings.telefono_contacto or "8095550000"
            session.flush()
            return
        session.add(
            TenantSettings(
                tenant_id=tenant_id,
                moneda="DOP",
                cuenta_ingresos="701-VENT",
                cuenta_itbis="208-ITBIS",
                cuenta_retenciones="209-RET",
                dias_credito=30,
                correo_facturacion="facturacion@demo.getupsoft.com.do",
                telefono_contacto="8095550000",
                notas="Seed publico para pruebas funcionales.",
            )
        )


def _ensure_invoice_seed(
    tenant_id: int,
    plan_id: int | None,
    *,
    encf: str,
    tipo_ecf: str,
    rnc_receptor: str,
    estado_dgii: str,
    track_id: str,
    total: Decimal,
    reference: str,
    description: str,
) -> None:
    with session_scope() as session:
        invoice = session.scalar(
            select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                Invoice.encf == encf,
            )
        )
        if not invoice:
            invoice = Invoice(
                tenant_id=tenant_id,
                encf=encf,
                tipo_ecf=tipo_ecf,
                rnc_receptor=rnc_receptor,
                xml_path=f"/var/getupsoft/storage/demo/{encf}.xml",
                xml_hash=f"demo-hash-{encf.lower()}",
                estado_dgii=estado_dgii,
                track_id=track_id,
                codigo_seguridad="123456",
                total=total,
            )
            session.add(invoice)
            session.flush()

        usage = session.scalar(
            select(UsageRecord).where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.track_id == track_id,
            )
        )
        if not usage:
            session.add(
                UsageRecord(
                    tenant_id=tenant_id,
                    plan_id=plan_id,
                    invoice_id=invoice.id,
                    ecf_type=tipo_ecf,
                    track_id=track_id,
                    monto_cargado=Decimal("3.50"),
                )
            )

        ledger = session.scalar(
            select(InvoiceLedgerEntry).where(
                InvoiceLedgerEntry.tenant_id == tenant_id,
                InvoiceLedgerEntry.referencia == reference,
            )
        )
        if not ledger:
            session.add(
                InvoiceLedgerEntry(
                    tenant_id=tenant_id,
                    invoice_id=invoice.id,
                    referencia=reference,
                    cuenta="701-VENT",
                    descripcion=description,
                    debit=Decimal("0.00"),
                    credit=total,
                )
            )
            invoice.contabilizado = True
            invoice.asiento_referencia = reference


def main() -> None:
    basic_plan = _ensure_plan(
        "Emprendedor",
        precio_mensual=Decimal("1490.00"),
        precio_por_documento=Decimal("3.50"),
        documentos_incluidos=500,
        max_facturas_mes=2500,
        max_facturas_por_receptor_mes=500,
        max_monto_por_factura=Decimal("500000.00"),
        includes_recurring_invoices=False,
        descripcion="Plan basico para emision y consulta. No incluye automatizacion recurrente.",
    )
    pro_plan = _ensure_plan(
        "Profesional",
        precio_mensual=Decimal("2990.00"),
        precio_por_documento=Decimal("3.00"),
        documentos_incluidos=2500,
        max_facturas_mes=7500,
        max_facturas_por_receptor_mes=800,
        max_monto_por_factura=Decimal("750000.00"),
        includes_recurring_invoices=True,
        descripcion="Plan Pro con automatizaciones operativas, incluyendo facturas recurrentes.",
    )
    platform_tenant = _ensure_tenant(
        name="Platform",
        rnc="00000000000",
        env="testecf",
        dgii_base_ecf=str(settings.dgii_recepcion_base_url),
        dgii_base_fc=str(settings.dgii_recepcion_fc_base_url),
        plan_id=basic_plan.id,
    )
    demo_tenant = _ensure_tenant(
        name="Empresa Demo",
        rnc="12345678901",
        env="testecf",
        dgii_base_ecf=str(settings.dgii_recepcion_base_url),
        dgii_base_fc=str(settings.dgii_recepcion_fc_base_url),
        plan_id=pro_plan.id,
    )
    reseller_tenant = _ensure_tenant(
        name="Cliente Seller Demo",
        rnc="12345678902",
        env="certecf",
        dgii_base_ecf=str(settings.dgii_recepcion_base_url),
        dgii_base_fc=str(settings.dgii_recepcion_fc_base_url),
        plan_id=pro_plan.id,
    )
    read_only_tenant = _ensure_tenant(
        name="Cliente Solo Lectura",
        rnc="12345678903",
        env="precert",
        dgii_base_ecf=str(settings.dgii_recepcion_base_url),
        dgii_base_fc=str(settings.dgii_recepcion_fc_base_url),
        plan_id=basic_plan.id,
    )
    seller_account = _ensure_partner_account(name="Seller Demo", slug="seller-demo")

    admin = _ensure_user(
        email="admin@getupsoft.com.do",
        password="ChangeMe123!",
        role="platform_superroot",
        phone="8095551000",
        tenant_id=platform_tenant.id,
    )
    client = _ensure_user(
        email="cliente@getupsoft.com.do",
        password="Tenant123!",
        role="tenant_user",
        phone="8095552000",
        tenant_id=demo_tenant.id,
    )
    client_operator = _ensure_user(
        email="cliente.operador@getupsoft.com.do",
        password="TenantOps123!",
        role="tenant_admin",
        phone="8095552001",
        tenant_id=reseller_tenant.id,
    )
    seller = _ensure_user(
        email="seller@getupsoft.com.do",
        password="Seller123!",
        role="partner_reseller",
        phone="8095553000",
        tenant_id=platform_tenant.id,
        partner_account_id=seller_account.id,
    )
    seller_operator = _ensure_user(
        email="seller.operator@getupsoft.com.do",
        password="SellerOps123!",
        role="partner_operator",
        phone="8095553001",
        tenant_id=platform_tenant.id,
        partner_account_id=seller_account.id,
    )
    seller_auditor = _ensure_user(
        email="seller.auditor@getupsoft.com.do",
        password="SellerAudit123!",
        role="partner_auditor",
        phone="8095553002",
        tenant_id=platform_tenant.id,
        partner_account_id=seller_account.id,
    )

    _ensure_tenant_settings(demo_tenant.id)
    _ensure_tenant_settings(reseller_tenant.id)
    _ensure_tenant_settings(read_only_tenant.id)
    _ensure_assignment(partner_account_id=seller_account.id, tenant_id=demo_tenant.id, can_emit=True, can_manage=True)
    _ensure_assignment(partner_account_id=seller_account.id, tenant_id=reseller_tenant.id, can_emit=True, can_manage=True)
    _ensure_assignment(partner_account_id=seller_account.id, tenant_id=read_only_tenant.id, can_emit=False, can_manage=False)
    _ensure_invoice_seed(
        demo_tenant.id,
        pro_plan.id,
        encf="E310000000001",
        tipo_ecf="31",
        rnc_receptor="101010101",
        estado_dgii="ACEPTADO",
        track_id="demo-track-001",
        total=Decimal("1500.00"),
        reference="ASI-DEMO-001",
        description="Asiento de demostracion cliente demo",
    )
    _ensure_invoice_seed(
        reseller_tenant.id,
        pro_plan.id,
        encf="E310000000002",
        tipo_ecf="31",
        rnc_receptor="131998887",
        estado_dgii="PENDIENTE",
        track_id="demo-track-002",
        total=Decimal("2890.50"),
        reference="ASI-DEMO-002",
        description="Asiento de demostracion seller demo",
    )
    _ensure_invoice_seed(
        read_only_tenant.id,
        basic_plan.id,
        encf="E310000000003",
        tipo_ecf="31",
        rnc_receptor="101112131",
        estado_dgii="RECHAZADO",
        track_id="demo-track-003",
        total=Decimal("990.00"),
        reference="ASI-DEMO-003",
        description="Asiento de demostracion cliente solo lectura",
    )

    print(
        "\n".join(
            [
                f"Platform tenant: {platform_tenant.id} {platform_tenant.name}",
                f"Demo tenant: {demo_tenant.id} {demo_tenant.name}",
                f"Seller tenant: {reseller_tenant.id} {reseller_tenant.name}",
                f"Read only tenant: {read_only_tenant.id} {read_only_tenant.name}",
                f"Admin user: {admin.email} ({admin.role})",
                f"Client user: {client.email} ({client.role})",
                f"Client operator: {client_operator.email} ({client_operator.role})",
                f"Seller user: {seller.email} ({seller.role})",
                f"Seller operator: {seller_operator.email} ({seller_operator.role})",
                f"Seller auditor: {seller_auditor.email} ({seller_auditor.role})",
                f"Partner account: {seller_account.id} {seller_account.slug}",
                f"Plan basico: {basic_plan.id} {basic_plan.name}",
                f"Plan pro: {pro_plan.id} {pro_plan.name}",
            ]
        )
    )


if __name__ == "__main__":
    main()
