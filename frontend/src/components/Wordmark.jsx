// Signature de marque, unique et partagée : page d'accueil et header affichent
// exactement le même lockup, seule la taille de base change.
//
// La hiérarchie fait tout le travail : "SBD" massif, lettres presque collées ;
// "Reviews" quatre fois plus petit, très espacé, aligné sur la même ligne de
// base. Pas de dégradé, pas de contour, pas de halo.
//
// Tout est dimensionné en `em` à partir de `root` : une seule valeur à changer
// pour redimensionner le lockup entier sans le déformer.
const SIZES = {
  sm: {
    root: 'text-[26px]',
    rule: 'w-6',
    slogan: 'text-[9px] tracking-[0.16em] sm:tracking-[0.2em]',
    gap: 'mt-2.5',
  },
  lg: {
    root: 'text-[44px] sm:text-[72px] xl:text-[88px]',
    rule: 'w-6 sm:w-10',
    slogan: 'text-[10px] sm:text-[11px] tracking-[0.14em] sm:tracking-[0.26em]',
    gap: 'mt-4 sm:mt-5',
  },
};

export default function Wordmark({ size = 'lg', showSlogan = true, className = '' }) {
  const s = SIZES[size] ?? SIZES.lg;

  return (
    <div className={ className }>
      <h1 className={ `flex items-baseline gap-[0.18em] leading-none ${ s.root }` }>
        <span className="font-black tracking-[-0.045em] text-white">SBD</span>
        {/* -mr compense l'espace que `tracking` ajoute après la dernière lettre :
            sans ça le lockup paraît décalé à gauche quand il est centré. */}
        <span className="-mr-[0.34em] text-[0.27em] font-black uppercase tracking-[0.34em] text-gray-400">
          Reviews
        </span>
      </h1>

      { showSlogan && (
        <div className={ `flex min-w-0 items-center gap-2 sm:gap-3 ${ s.gap }` }>
          <span className={ `h-px flex-shrink-0 bg-emerald-400 ${ s.rule }` } />
          <span className={ `min-w-0 font-bold uppercase text-gray-400 ${ s.slogan }` }>
            Strength built on perfect technique
          </span>
        </div>
      ) }
    </div>
  );
}
