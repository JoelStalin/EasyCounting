import React, { useState } from 'react';
import axios from 'axios';

const plans = [
  {
    target: 'Persona',
    title: 'Individual / Profesional',
    features: ['Acceso Básico Web', 'Emisión e-CF', 'Soporte Básico', 'Dashboard Mensual'],
    price: 'RD$ 900 / mes',
    color: 'border-blue-500',
    headerBg: 'bg-blue-50',
  },
  {
    target: 'Negocios',
    title: 'Pymes / Negocios',
    features: [
      'Todo lo de Persona',
      'Facturador Múltiple',
      'Declaraciones Juradas (CS1, ITBIS)',
      'Automatización OFV Base',
    ],
    price: 'RD$ 3,500 / mes',
    color: 'border-purple-500',
    headerBg: 'bg-purple-50',
    highlight: true,
  },
  {
    target: 'Socios',
    title: 'Enterprise / Socios',
    features: [
      'Declaraciones Automatizadas Premium',
      'Buzón DGII Sincronizado',
      'Integración Odoo ERP',
      'Soporte 24/7 y Gestión Documental',
    ],
    price: 'A Medida',
    color: 'border-emerald-500',
    headerBg: 'bg-emerald-50',
  },
];

const adminRoles = ['Root', 'Admin de Plataforma'];

export default function SubscriptionPlans() {
  const [activeTab, setActiveTab] = useState('clientes'); // 'clientes' o 'admin'
  const [dgiiStatus, setDgiiStatus] = useState(null);

  const checkDGIICertification = async () => {
    try {
      const response = await axios.post('/api/v1/dgii/certification/status', {
        rnc: '22500706423',
        password: 'dummy'
      });
      setDgiiStatus(response.data);
      alert(`Estado DGII: ${response.data.certification_state} - ${response.data.message}`);
    } catch (e) {
      alert("Error verificando DGII: " + (e.response?.data?.detail || e.message));
    }
  };

  return (
    <div className="flex flex-col w-full h-full p-6 lg:p-12 bg-gray-50 overflow-auto">
      <div className="flex flex-col mb-10 text-center">
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Gestión de Planes y Servicios</h1>
        <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
          Personaliza y configura los niveles de acceso para la automatización de la Oficina Virtual DGII y servicios de Facturación.
        </p>
      </div>

      <div className="flex justify-center mb-8">
        <div className="inline-flex bg-gray-200 rounded-lg p-1">
          <button
            className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'clientes' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => setActiveTab('clientes')}
          >
            Planes de Clientes (SaaS)
          </button>
          <button
            className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'admin' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => setActiveTab('admin')}
          >
            Configuración Admin/Root
          </button>
        </div>
      </div>

      {activeTab === 'clientes' ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {plans.map((plan, idx) => (
            <div
              key={idx}
              className={`bg-white rounded-2xl shadow-xl flex flex-col overflow-hidden border-t-8 transition-transform transform hover:-translate-y-2 ${plan.color}`}
            >
              <div className={`p-8 ${plan.headerBg}`}>
                <h3 className="text-xl font-bold text-gray-900 font-display">{plan.title}</h3>
                <p className="text-sm text-gray-500 font-medium tracking-wide uppercase mt-1">Para {plan.target}</p>
                <div className="mt-4 flex items-baseline text-3xl font-extrabold text-gray-900">
                  {plan.price}
                </div>
              </div>
              <div className="p-8 flex-1 flex flex-col justify-between">
                <ul className="space-y-4">
                  {plan.features.map((feature, fidx) => (
                    <li key={fidx} className="flex items-start">
                      <svg className="flex-shrink-0 h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="ml-3 text-base text-gray-700 leading-tight">{feature}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-8 flex flex-col gap-3">
                  <button className="w-full bg-gray-900 text-white rounded-lg py-3 px-4 font-semibold hover:bg-gray-800 transition-colors shadow-md">
                    Configurar Plan
                  </button>
                  {plan.target === 'Negocios' && (
                    <button 
                      onClick={checkDGIICertification}
                      className="w-full bg-green-600 text-white rounded-lg py-3 px-4 font-semibold hover:bg-green-700 transition-colors shadow-md"
                    >
                      Verificar Estado DGII
                    </button>
                  )}
                  {dgiiStatus && plan.target === 'Negocios' && (
                    <div className="p-3 bg-green-100 text-sm text-green-800 rounded-md">
                      Paso {dgiiStatus.step}: {dgiiStatus.certification_state}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg border border-gray-100 p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 border-b pb-4">Roles Internos de Gestión</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="p-6 bg-red-50 rounded-lg border border-red-100">
              <h3 className="text-xl font-bold text-red-800 mb-2">Usuario Root</h3>
              <p className="text-gray-700 text-sm mb-4">Acceso global al sistema, clústeres de base de datos, facturador base y código fuente de Odoo/Certia.</p>
              <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
                <li>Gestión de Certificados .P12 Globales</li>
                <li>Ver Logs del OFV Scraper</li>
                <li>Gestión Multi-Tenant</li>
              </ul>
            </div>
            <div className="p-6 bg-indigo-50 rounded-lg border border-indigo-100">
              <h3 className="text-xl font-bold text-indigo-800 mb-2">Administrador</h3>
              <p className="text-gray-700 text-sm mb-4">Gestión de suscripciones, aprobaciones de cuentas de usuarios, y roles comerciales.</p>
              <ul className="list-disc list-inside text-sm text-indigo-700 space-y-1">
                <li>Autorizar Facturación a Socios</li>
                <li>Suspender automatización OFV</li>
                <li>Soporte al Contribuyente</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
