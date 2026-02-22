import { Outlet, NavLink, useLocation } from 'react-router-dom';

const NaturalGas = () => {
  const location = useLocation();
  const basePath = '/market/natural-gas';

  const tabs = [
    { to: `${basePath}/overview`, label: 'Overview' },
    { to: `${basePath}/prices`, label: 'Prices & Basis' },
    { to: `${basePath}/storage`, label: 'Storage' },
    { to: `${basePath}/pipelines`, label: 'Pipelines' },
    { to: `/finance/pipelines`, label: 'Financials (FERC 2)' },
    { to: `/finance/transactions`, label: 'Transactions (FERC 552)' },
  ];

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex items-center gap-6 border-b border-gray-700 pb-4">
        <h2 className="text-2xl font-bold text-white">Natural Gas Market</h2>
        <nav className="flex gap-1 ml-4">
          {tabs.map(({ to, label }) => {
            const isActive = location.pathname === to || location.pathname.startsWith(to + '/');
            return (
              <NavLink
                key={to}
                to={to}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                {label}
              </NavLink>
            );
          })}
        </nav>
      </div>
      <div className="flex-1 min-h-0">
        <Outlet />
      </div>
    </div>
  );
};

export default NaturalGas;
