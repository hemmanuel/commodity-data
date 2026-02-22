import { Outlet, NavLink, useLocation } from 'react-router-dom';

const NaturalGasLayout = () => {
  const location = useLocation();
  const basePath = '/natural-gas';

  const subNavItems = [
    { to: `${basePath}/storage`, label: 'Storage (EIA)' },
    { to: `${basePath}/financials`, label: 'Financials (FERC Form 2)' },
    { to: `${basePath}/transactions`, label: 'Transactions (FERC Form 552)' },
    { to: `${basePath}/data`, label: 'Data Browser (EIA)' },
  ];

  return (
    <div className="space-y-6 h-[calc(100vh-100px)] flex flex-col">
      <div className="flex flex-col gap-4 border-b border-gray-700 pb-4">
        <h2 className="text-2xl font-bold text-white">Natural Gas</h2>
        <nav className="flex gap-1 overflow-x-auto">
          {subNavItems.map(({ to, label }) => {
            const isActive = location.pathname === to || location.pathname.startsWith(to + '/');
            return (
              <NavLink
                key={to}
                to={to}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
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

export default NaturalGasLayout;
