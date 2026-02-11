export default function MinimalFooter() {
    return (
        <footer className="py-24 px-6 md:px-12 max-w-7xl mx-auto border-t border-neutral-200 text-center font-sans tracking-tight text-neutral-400 text-sm font-light">
            <p className="uppercase tracking-widest text-neutral-900 font-medium mb-4">Odor Finium</p>
            <div className="space-y-2">
                <p>Magyarországon tervezve</p>
                <p>© {new Date().getFullYear()}</p>
            </div>
        </footer>
    );
}
