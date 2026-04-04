'use client';

import { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { X, Camera } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { createClient } from '@/lib/supabase/client';
import styles from './page.module.css';

const CATEGORIES = ['Tops', 'Bottoms', 'Shoes', 'Outerwear', 'Accessories', 'Bags'];
const AVAILABLE_TAGS = ['Casual', 'Business', 'Formal', 'Summer', 'Winter', 'Sport', 'Evening', 'Weekend'];
const FABRIC_OPTIONS = ['Cotton', 'Linen', 'Wool', 'Silk', 'Polyester', 'Denim', 'Leather', 'Other'];

type PhotoEntry = {
  id: string;
  originalUrl: string;
  processedUrl?: string;
  processing: boolean;
};

export default function AddItemPageClient() {
  const router = useRouter();
  const supabase = createClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [photos, setPhotos] = useState<PhotoEntry[]>([]);
  const [category, setCategory] = useState('');
  const [color, setColor] = useState('');
  const [fabric, setFabric] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // ──────────────────────────────────────────────────────────────────────────
  // Photo handling — runs 100% in the browser, no server involved
  // ──────────────────────────────────────────────────────────────────────────
  const handleFilesChosen = useCallback(async (files: FileList) => {
    const fileArray = Array.from(files);

    const newEntries: PhotoEntry[] = fileArray.map((file) => ({
      id: crypto.randomUUID(),
      originalUrl: URL.createObjectURL(file),
      processing: true,
    }));

    setPhotos((prev) => [...prev, ...newEntries]);

    // Process each photo through @imgly/background-removal
    for (let i = 0; i < fileArray.length; i++) {
      const entry = newEntries[i];
      const file = fileArray[i];
      try {
        // Dynamic import ensures the WASM is only loaded in the browser
        const { removeBackground } = await import('@imgly/background-removal');
        const blob = await removeBackground(file);
        const processedUrl = URL.createObjectURL(blob);
        setPhotos((prev) =>
          prev.map((p) => p.id === entry.id ? { ...p, processedUrl, processing: false } : p)
        );
      } catch {
        // Fallback: use original photo if background removal fails
        setPhotos((prev) =>
          prev.map((p) => p.id === entry.id ? { ...p, processing: false } : p)
        );
      }
    }
  }, []);

  const removePhoto = useCallback((id: string) => {
    setPhotos((prev) => prev.filter((p) => p.id !== id));
  }, []);

  const toggleTag = useCallback((tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }, []);

  // ──────────────────────────────────────────────────────────────────────────
  // Save to Supabase
  // ──────────────────────────────────────────────────────────────────────────
  const handleSave = async () => {
    if (!category) { setError('Please select a category.'); return; }
    setSaving(true);
    setError('');

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('You must be logged in.');

      const uploadedUrls: string[] = [];
      for (const photo of photos) {
        const displayUrl = photo.processedUrl ?? photo.originalUrl;
        const response = await fetch(displayUrl);
        const blob = await response.blob();
        const ext = blob.type === 'image/png' ? 'png' : 'jpg';
        const path = `${user.id}/${crypto.randomUUID()}.${ext}`;

        const { error: uploadError } = await supabase.storage
          .from('wardrobe-images')
          .upload(path, blob, { contentType: blob.type });

        if (uploadError) throw uploadError;

        const { data: urlData } = supabase.storage
          .from('wardrobe-images')
          .getPublicUrl(path);

        uploadedUrls.push(urlData.publicUrl);
      }

      const { error: insertError } = await supabase
        .from('wardrobe_items')
        .insert({
          user_id: user.id,
          category: category.toLowerCase(),
          color: color || null,
          fabric: fabric || null,
          tags: selectedTags,
          image_urls: uploadedUrls,
          is_archived: false,
        });

      if (insertError) throw insertError;

      router.push('/wardrobe');
      router.refresh();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.header}>
        <button className={styles.cancelBtn} onClick={() => router.back()}>Cancel</button>
        <h1 className={styles.title}>New Piece</h1>
        <button className={styles.saveBtn} onClick={handleSave} disabled={!category || saving}>
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>

      <div className={styles.body}>
        {error && <div className={styles.errorBanner}>{error}</div>}

        {/* Photos */}
        <div className={styles.photoSection}>
          <p className={styles.sectionLabel}>Photos</p>
          <div className={styles.photoRow}>
            {photos.map((photo) => (
              <div key={photo.id} className={styles.photoThumb}>
                <img
                  src={photo.processedUrl ?? photo.originalUrl}
                  alt="Wardrobe item"
                  className={styles.photoThumbImg}
                />
                {photo.processing && (
                  <div className={styles.processingBadge}>
                    <div className={styles.spinner} />
                    <span>Removing bg…</span>
                  </div>
                )}
                {!photo.processing && (
                  <button className={styles.removePhoto} onClick={() => removePhoto(photo.id)} aria-label="Remove photo">
                    <X size={12} strokeWidth={3} />
                  </button>
                )}
              </div>
            ))}
            {photos.length < 5 && (
              <button className={styles.addPhotoBtn} onClick={() => fileInputRef.current?.click()}>
                <Camera size={20} />
                <span>Add Photo</span>
              </button>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            capture="environment"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files && handleFilesChosen(e.target.files)}
          />
        </div>

        {/* Category */}
        <div className={styles.field}>
          <p className={styles.sectionLabel}>Category *</p>
          <select className={styles.select} value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">Select category…</option>
            {CATEGORIES.map((c) => <option key={c} value={c.toLowerCase()}>{c}</option>)}
          </select>
        </div>

        {/* Colour */}
        <div className={styles.field}>
          <Input label="Colour" placeholder="e.g. Navy Blue" value={color} onChange={(e) => setColor(e.target.value)} />
        </div>

        {/* Fabric */}
        <div className={styles.field}>
          <p className={styles.sectionLabel}>Fabric</p>
          <select className={styles.select} value={fabric} onChange={(e) => setFabric(e.target.value)}>
            <option value="">Select fabric…</option>
            {FABRIC_OPTIONS.map((f) => <option key={f} value={f.toLowerCase()}>{f}</option>)}
          </select>
        </div>

        {/* Tags */}
        <div className={styles.field}>
          <p className={styles.sectionLabel}>Tags</p>
          <div className={styles.tagGrid}>
            {AVAILABLE_TAGS.map((tag) => (
              <button
                key={tag}
                className={`${styles.tagChip} ${selectedTags.includes(tag) ? styles.tagChipActive : ''}`}
                onClick={() => toggleTag(tag)}
                aria-pressed={selectedTags.includes(tag)}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
