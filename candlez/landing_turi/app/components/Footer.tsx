export default function Footer() {
    return (
        <footer className="py-12 px-6 md:px-12 border-t border-white/5 mt-12">
            <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center text-xs text-neutral-600 font-mono gap-4">
                <span>Odor Finium</span>
                <span>Designed in Budapest</span>
                <span>© {new Date().getFullYear()}</span>
            </div>
        </footer>
    );
}
