from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple
import datetime
from methods.utils import read_json_file, write_json_file

@dataclass
class Profile:
    user_id: int
    full_name: str
    ort_score: int
    timestamp: str = None

class ProfileManager:
    def __init__(self):
        self.profiles_file = "profiles.json"
        self.pending_file = "pending_profiles.json"
        self.default_profiles = {"profiles": {}}
        self.default_pending = {"pending": {}}

    def _read_profiles(self) -> Dict:
        return read_json_file(self.profiles_file, self.default_profiles)

    def _write_profiles(self, data: Dict) -> None:
        write_json_file(self.profiles_file, data)

    def _read_pending_profiles(self) -> Dict:
        return read_json_file(self.pending_file, self.default_pending)

    def _write_pending_profiles(self, data: Dict) -> None:
        write_json_file(self.pending_file, data)

    async def get_profile(self, user_id: int) -> Optional[Dict]:
        data = self._read_profiles()
        profile = data["profiles"].get(str(user_id))
        if profile:
            return {
                "user_id": user_id,
                "full_name": profile["full_name"],
                "ort_score": profile["ort_score"]
            }
        return None

    async def add_pending_profile(self, user_id: int, full_name: str, ort_score: int) -> None:
        profile = Profile(
            user_id=user_id,
            full_name=full_name,
            ort_score=ort_score,
            timestamp=datetime.datetime.now().isoformat()
        )
        data = self._read_pending_profiles()
        data["pending"][str(user_id)] = profile.__dict__
        self._write_pending_profiles(data)

    async def format_profile(self, profile: Dict, rank: int, total: int, lang: str) -> str:
        if not profile:
            return self.get_message("profile_not_found", lang)
        return self.get_message("profile_template", lang).format(
            name=profile['full_name'],
            score=profile['ort_score'],
            rank=rank if rank else "N/A",
            total=total
        )

    async def format_rankings(self, user_id: int, lang: str, top_count: int = 10) -> str:
        rankings = await self.get_rankings()
        user_rank, total = await self.get_user_rank(user_id)
        
        text = self.get_message("rankings_header", lang) + "\n\n"
        
        for i, profile in enumerate(rankings[:top_count], 1):
            text += self.get_message("ranking_line", lang).format(
                pos=i,
                name=profile['full_name'],
                score=profile['ort_score']
            )
        
        if user_rank and user_rank > top_count:
            text += self.get_message("user_ranking_line", lang).format(
                rank=user_rank,
                name=rankings[user_rank-1]['full_name'],
                score=rankings[user_rank-1]['ort_score']
            )
        
        text += self.get_message("total_participants", lang).format(total=total)
        return text

    async def get_rankings(self) -> List[Dict]:
        data = self._read_profiles()
        profiles = data["profiles"]
        
        rankings = [
            {"user_id": int(uid), **profile} 
            for uid, profile in profiles.items()
        ]
        return sorted(rankings, key=lambda x: x["ort_score"], reverse=True)

    async def get_user_rank(self, user_id: int) -> Tuple[Optional[int], int]:
        rankings = await self.get_rankings()
        total = len(rankings)
        
        for idx, profile in enumerate(rankings, 1):
            if profile["user_id"] == user_id:
                return idx, total
                
        return None, total

    async def approve_profile(self, user_id: int) -> bool:
        pending_data = self._read_pending_profiles()
        pending = pending_data["pending"].get(str(user_id))
        
        if not pending:
            return False
            
        await self.update_profile(user_id, pending["full_name"], pending["ort_score"])
        
        del pending_data["pending"][str(user_id)]
        self._write_pending_profiles(pending_data)
        return True

    async def reject_profile(self, user_id: int) -> bool:
        pending_data = self._read_pending_profiles()
        if str(user_id) in pending_data["pending"]:
            del pending_data["pending"][str(user_id)]
            self._write_pending_profiles(pending_data)
            return True
        return False

    async def update_profile(self, user_id: int, full_name: str, ort_score: int) -> None:
        data = self._read_profiles()
        data["profiles"][str(user_id)] = {
            "full_name": full_name,
            "ort_score": ort_score
        }
        self._write_profiles(data)

    async def get_pending_profiles(self) -> List[Dict]:
        data = self._read_pending_profiles()
        result = []
        for user_id, profile_data in data["pending"].items():
            profile_data["user_id"] = int(user_id)
            result.append(profile_data)
        return result

    MESSAGES = {
        "profile_not_found": {
            "ru": "❌ Профиль не найден.\nХотите создать новый профиль?",
            "kg": "❌ Профиль табылган жок.\nЖаңы профиль түзгүңүз келеби?"
        },
        "profile_template": {
            "ru": "📋 Ваш профиль:\n\n👤 ФИО: {name}\n📊 Балл ОРТ: {score}\n🏆 Место в рейтинге: {rank}/{total}",
            "kg": "📋 Сиздин профилиңиз:\n\n👤 ФАА: {name}\n📊 ЖРТ баллы: {score}\n🏆 Рейтингдеги орун: {rank}/{total}"
        },
        "update_profile": {
            "ru": "Обновить профиль",
            "kg": "Профилди жаңыртуу"
        },
        "rating": {
            "ru": "Рейтинг",
            "kg": "Рейтинг"
        },
        "yes": {
            "ru": "✅ Да",
            "kg": "✅ Ооба"
        },
        "no": {
            "ru": "❌ Нет",
            "kg": "❌ Жок"
        },
        "menu": {
            "ru": "Главное меню",
            "kg": "Башкы меню"
        },
        "enter_full_name": {
            "ru": "Введите ваше ФИО:",
            "kg": "ФААңызды жазыңыз:"
        },
        "enter_score": {
            "ru": "Введите ваш балл ОРТ (от 0 до 245):",
            "kg": "ЖРТ баллыңызды жазыңыз (0дон 245ге чейин):"
        },
        "invalid_score": {
            "ru": "❌ Неверный формат балла. Введите число от 0 до 245.",
            "kg": "❌ Туура эмес балл. 0дон 245ге чейинки санды жазыңыз."
        },
        "profile_submitted": {
            "ru": "✅ Ваш профиль отправлен на проверку.",
            "kg": "✅ Сиздин профилиңиз текшерүүгө жөнөтүлдү."
        },
        "profile_creation_rejected": {
            "ru": "❌ Создание профиля отменено.",
            "kg": "❌ Профиль түзүү жокко чыгарылды."
        },
        "error_occurred": {
            "ru": "❌ Произошла ошибка. Попробуйте позже.",
            "kg": "❌ Ката кетти. Кийинчерээк кайталаңыз."
        },
        "approve": {
            "ru": "✅ Подтвердить",
            "kg": "✅ Тастыктоо"
        },
        "reject": {
            "ru": "❌ Отклонить",
            "kg": "❌ Четке кагуу"
        },
        "new_profile_admin": {
            "ru": "📝 Новый профиль от {user}:\n👤 ФИО: {name}\n📊 Балл ОРТ: {score}",
            "kg": "📝 Жаңы профиль {user}:\n👤 ФАА: {name}\n📊 ЖРТ баллы: {score}"
        },
        "rankings_header": {
            "ru": "🏆 Рейтинг по баллам ОРТ:",
            "kg": "🏆 ЖРТ баллдары боюнча рейтинг:"
        },
        "ranking_line": {
            "ru": "{pos}. {name} - {score} баллов\n",
            "kg": "{pos}. {name} - {score} балл\n"
        },
        "user_ranking_line": {
            "ru": "\n... Ваше место: {rank}. {name} - {score} баллов\n",
            "kg": "\n... Сиздин орунуңуз: {rank}. {name} - {score} балл\n"
        },
        "total_participants": {
            "ru": "\n\nВсего участников: {total}",
            "kg": "\n\nБардык катышуучулар: {total}"
        }
    }

    def get_message(self, key: str, lang: str) -> str:
        return self.MESSAGES.get(key, {}).get(lang, "Message not found")