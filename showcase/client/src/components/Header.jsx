import { Link, useLocation } from 'react-router-dom';

export default function Header() {
  const location = useLocation();

  const links = [
    { to: '/', label: 'Dashboard' },
    { to: '/new', label: 'New Review' },
    { to: '/analytics', label: 'Analytics' },
  ];

  return (
    <header className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-harnessa-500 flex items-center justify-center text-white font-bold text-sm">
              H
            </div>
            <span className="text-xl font-bold text-white">
              Harnessa
            </span>
            <span className="hidden sm:inline text-sm text-gray-400 ml-1">
              Code Review Dashboard
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            {links.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === link.to
                    ? 'bg-harnessa-500/20 text-harnessa-300'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
