"""Metakognitív kalibráció és Brier Score számítási motor."""

from typing import Any, Dict, List, Optional


class CalibrationEngine:
    """
    A játékos önértékelési pontosságának (Confidence Calibration) és 
    Brier Score-jának egzakt matematikai számításai.
    """

    @staticmethod
    def calculate_brier_score(answers: List[Dict[str, Any]]) -> Optional[float]:
        """
        Kiszámítja a Brier Score-t: BS = (1/N) * sum((f_t - o_t)^2)
        ahol f_t a magabiztosság (0.0 - 1.0), o_t a helyesség (1 vagy 0).
        0.0 = tökéletes jóslás és helyesség.
        0.25 = 50%-os véletlen találgatás.
        Nagyobb érték = rossz kalibráció.
        """
        if not answers:
            return None

        total_sq_error = 0.0
        for a in answers:
            f_t = float(a["confidence_level"])
            o_t = 1.0 if a["is_correct"] else 0.0
            total_sq_error += (f_t - o_t) ** 2

        return round(total_sq_error / len(answers), 4)

    @staticmethod
    def calculate_accuracy(answers: List[Dict[str, Any]]) -> float:
        """Kiszámítja a válaszok tényleges helyességi arányát (0.0 - 1.0)."""
        if not answers:
            return 0.0
        correct_count = sum(1 for a in answers if a.get("is_correct"))
        return round(correct_count / len(answers), 4)

    @staticmethod
    def calculate_bias(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Kiszámítja az átlagos magabiztossági torzítást (Confidence Bias):
        Bias = (1/N) * sum(f_t - o_t)
        Ha Bias > +0.05: Túlzott önbizalom (Overconfidence).
        Ha Bias < -0.05: Kishitűség (Underconfidence).
        Közötte: Jól kalibrált (Well-calibrated).
        """
        if not answers:
            return {
                "bias": 0.0,
                "avg_confidence": 0.0,
                "accuracy": 0.0,
                "type": "well_calibrated",
                "label": "Nincs még elegendő adat"
            }

        avg_conf = sum(float(a["confidence_level"]) for a in answers) / len(answers)
        acc = sum(1.0 if a["is_correct"] else 0.0 for a in answers) / len(answers)
        bias = round(avg_conf - acc, 4)

        if bias > 0.08:
            bias_type = "overconfident"
            label = "⚠️ Túlzott önbizalom (Overconfidence)"
            advice = "Gyakran magabiztosabban tippelsz, mint amennyire valójában tudod. Kocsmakvízben ez veszélyes lehet!"
        elif bias < -0.08:
            bias_type = "underconfident"
            label = "🛡️ Kishitűség (Underconfidence)"
            advice = "Többet tudsz, mint amennyire hiszed! Bízz jobban a megérzéseidben, és merd bemondani a csapatnak."
        else:
            bias_type = "well_calibrated"
            label = "🎯 Kiválóan kalibrált"
            advice = "A magabiztosságod hűen tükrözi a valós tudásodat. Ideális csapattárs vagy!"

        return {
            "bias": bias,
            "avg_confidence": round(avg_conf, 4),
            "accuracy": round(acc, 4),
            "type": bias_type,
            "label": label,
            "advice": advice
        }

    @staticmethod
    def calculate_calibration_curve(
        answers: List[Dict[str, Any]],
        n_bins: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Kalibrációs görbe pontjainak generálása magabiztossági sávok (binek) szerint.
        Minden sávban összeveti a feltételezett esélyt a valós sikerességgel.
        """
        if not answers:
            return []

        bins = []
        bin_width = 1.0 / n_bins
        for i in range(n_bins):
            low = i * bin_width
            high = (i + 1) * bin_width
            # Zárt intervallum az utolsónál [0.8, 1.0]
            bin_answers = [
                a for a in answers 
                if (low <= a["confidence_level"] <= high if i == n_bins - 1 else low <= a["confidence_level"] < high)
            ]

            bin_count = len(bin_answers)
            if bin_count > 0:
                avg_conf = sum(a["confidence_level"] for a in bin_answers) / bin_count
                acc = sum(1.0 if a["is_correct"] else 0.0 for a in bin_answers) / bin_count
            else:
                avg_conf = (low + high) / 2.0
                acc = None  # Nincs még adat ebben a sávban

            bins.append({
                "bin_index": i,
                "bin_range": f"{int(low * 100)}% - {int(high * 100)}%",
                "expected_prob": round((low + high) / 2.0, 2),
                "avg_confidence": round(avg_conf, 3) if avg_conf is not None else None,
                "accuracy": round(acc, 3) if acc is not None else None,
                "sample_count": bin_count
            })

        return bins

    @staticmethod
    def calculate_skill_matrix(answers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Képességmátrix generálása Domain és Mechanism bontásban.
        Megmutatja, melyik témakörökben és kérdéstípusokban a legerősebb vagy leginkább tévedő a játékos.
        """
        if not answers:
            return []

        grouped: Dict[tuple, List[Dict[str, Any]]] = {}
        for a in answers:
            key = (a.get("domain", "general"), a.get("mechanism", "abcd"))
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(a)

        matrix = []
        for (dom, mech), group in grouped.items():
            count = len(group)
            acc = sum(1.0 if a["is_correct"] else 0.0 for a in group) / count
            avg_conf = sum(a["confidence_level"] for a in group) / count
            bs = CalibrationEngine.calculate_brier_score(group)

            matrix.append({
                "domain": dom,
                "mechanism": mech,
                "sample_count": count,
                "accuracy": round(acc, 3),
                "avg_confidence": round(avg_conf, 3),
                "brier_score": bs,
                "bias": round(avg_conf - acc, 3)
            })

        # Rendezés a mintaszám, majd a pontosság szerint
        matrix.sort(key=lambda x: (x["sample_count"], x["accuracy"]), reverse=True)
        return matrix
