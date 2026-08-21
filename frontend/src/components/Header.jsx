export default function Header({ user, onOpenProfile }) {
  return (
    <header className="flex justify-between items-center mb-8 pb-6 border-b border-gray-800">
      <div>
        <h1 className="text-3xl font-black uppercase tracking-widest bg-gradient-to-r from-white to-gray-500 bg-clip-text text-transparent">
          SBD Reviews
        </h1>
        <p className="text-gray-400 text-sm mt-1">Strength built on perfect technique</p>
      </div>

      { user && (
        <button 
          onClick={ onOpenProfile }
          className="flex items-center gap-3 bg-gray-900 hover:bg-gray-800 border border-gray-800 p-2 pr-4 rounded-full transition-all group"
        >
          <div className="w-8 h-8 bg-gradient-to-tr from-emerald-500 to-teal-400 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-inner">
            { user.email.charAt(0).toUpperCase() }
          </div>
          <div className="flex flex-col items-start">
            <span className="text-xs font-semibold text-white group-hover:text-emerald-400 transition-colors">My Profile</span>
            <span className={ `text-[10px] uppercase font-bold tracking-wider ${ user.plan === 'premium' ? 'text-emerald-500' : 'text-gray-500' }` }>
              { user.plan }
            </span>
          </div>
        </button>
      ) }
    </header>
  );
}