-- Pattern detection: yanlis cevapta secilen distractor'in diag etiketi.
-- Bu sayede 'kullanici sik sik particle_eksik hatasi yapiyor' gibi insight cikar.

ALTER TABLE answer_log ADD COLUMN chosen_distractor_diag TEXT;

CREATE INDEX IF NOT EXISTS idx_answer_log_diag
    ON answer_log(chosen_distractor_diag, asked_at DESC)
    WHERE chosen_distractor_diag IS NOT NULL;
