import { Link, NavLink } from "react-router-dom";

type DemoStoreNavProps = {
  cartCount?: number;
  googleEnabled?: boolean;
  onGoogleClick?: () => void;
};

export function DemoStoreNav({ cartCount = 0, googleEnabled = false, onGoogleClick }: DemoStoreNavProps) {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-amber-200/10 bg-slate-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/catalog" className="flex items-center gap-3 text-white">
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-amber-300/40 bg-amber-300/10 text-sm font-semibold text-amber-200">
            GJ
          </div>
          <div>
            <p className="text-sm font-semibold">Galante's Jewelry</p>
            <p className="text-xs text-slate-400">Demo comercial y flujo de ventas</p>
          </div>
        </Link>

        <nav className="hidden items-center gap-6 text-sm text-slate-300 md:flex">
          <NavLink className={({ isActive }) => (isActive ? "text-amber-200" : "hover:text-white")} to="/catalog">
            Catalogo
          </NavLink>
          <NavLink className={({ isActive }) => (isActive ? "text-amber-200" : "hover:text-white")} to="/checkout">
            Cotizacion
          </NavLink>
          <NavLink className={({ isActive }) => (isActive ? "text-amber-200" : "hover:text-white")} to="/login">
            Acceso clientes
          </NavLink>
        </nav>

        <div className="flex items-center gap-3">
          <Link className="rounded-full border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-amber-200 hover:text-white" to="/checkout">
            Carrito {cartCount > 0 ? `(${cartCount})` : ""}
          </Link>
          {googleEnabled && onGoogleClick ? (
            <button
              type="button"
              onClick={onGoogleClick}
              className="rounded-full bg-amber-200 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-amber-100"
            >
              Crear cuenta con Google
            </button>
          ) : null}
        </div>
      </div>
    </header>
  );
}
