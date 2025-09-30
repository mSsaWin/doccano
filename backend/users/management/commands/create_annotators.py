import csv
import secrets
import string
from pathlib import Path
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from projects.models import Project, Member
from roles.models import Role


class Command(BaseCommand):
    help = 'Создает пользователей-аннотаторов из списка ФИО и добавляет их в проект'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            required=True,
            help='ID проекта, в который нужно добавить пользователей'
        )
        parser.add_argument(
            '--input',
            type=str,
            required=True,
            help='Путь к файлу со списком ФИО (текстовый файл или CSV, каждая строка - одно ФИО)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='annotators_credentials.xlsx',
            help='Имя выходного Excel файла (по умолчанию: annotators_credentials.xlsx)'
        )

    # Таблица транслитерации
    TRANSLIT_TABLE = {
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }

    def read_names_from_file(self, file_path):
        """Читает список ФИО из файла (текстовый или CSV)"""
        path = Path(file_path)
        
        if not path.exists():
            raise CommandError(f'Файл не найден: {file_path}')
        
        names = []
        
        # Определяем тип файла по расширению
        if path.suffix.lower() == '.csv':
            # Читаем CSV файл
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():  # Пропускаем пустые строки
                        names.append(row[0].strip())
        else:
            # Читаем как текстовый файл (каждая строка - одно ФИО)
            with open(path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Пропускаем пустые строки
                        names.append(line)
        
        if not names:
            raise CommandError(f'Файл пустой или не содержит корректных данных: {file_path}')
        
        return names

    def transliterate(self, text):
        """Транслитерация русского текста в латиницу"""
        result = []
        for char in text:
            result.append(self.TRANSLIT_TABLE.get(char, char))
        return ''.join(result)

    def generate_password(self, length=15):
        """Генерирует случайный пароль указанной длины"""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password

    def create_user_data(self, full_name):
        """Создает данные пользователя на основе ФИО"""
        parts = full_name.strip().split()
        surname = parts[0]
        
        # Транслитерация и приведение к нижнему регистру
        username = self.transliterate(surname).lower()
        
        # Если такой логин уже существует, добавляем номер
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        password = self.generate_password()
        
        return {
            'full_name': full_name,
            'username': username,
            'password': password
        }

    def create_excel_report(self, users_data, output_file):
        """Создает Excel файл с данными пользователей"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Учетные данные"
        
        # Заголовки
        headers = ['№', 'ФИО', 'Логин', 'Пароль']
        ws.append(headers)
        
        # Форматирование заголовков
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Данные пользователей
        for idx, user_data in enumerate(users_data, start=1):
            ws.append([
                idx,
                user_data['full_name'],
                user_data['username'],
                user_data['password']
            ])
        
        # Настройка ширины столбцов
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20
        
        wb.save(output_file)
        self.stdout.write(self.style.SUCCESS(f'Excel файл сохранен: {output_file}'))

    def handle(self, *args, **options):
        project_id = options['project_id']
        input_file = options['input']
        output_file = options['output']
        
        # Читаем список ФИО из файла
        try:
            names_list = self.read_names_from_file(input_file)
            self.stdout.write(self.style.SUCCESS(f'Прочитано {len(names_list)} записей из файла: {input_file}'))
        except Exception as e:
            raise CommandError(f'Ошибка чтения файла: {str(e)}')
        
        # Проверяем существование проекта
        try:
            project = Project.objects.get(id=project_id)
            self.stdout.write(self.style.SUCCESS(f'Проект найден: {project.name} (ID: {project_id})'))
        except Project.DoesNotExist:
            raise CommandError(f'Проект с ID {project_id} не найден')
        
        # Получаем роль аннотатора
        try:
            annotator_role = Role.objects.get(name=settings.ROLE_ANNOTATOR)
            self.stdout.write(self.style.SUCCESS(f'Роль аннотатора найдена: {annotator_role.name}'))
        except Role.DoesNotExist:
            raise CommandError(f'Роль "{settings.ROLE_ANNOTATOR}" не найдена в базе данных')
        
        users_data = []
        created_count = 0
        skipped_count = 0
        
        self.stdout.write('\nСоздание пользователей:')
        self.stdout.write('-' * 80)
        
        for full_name in names_list:
            user_data = self.create_user_data(full_name)
            
            try:
                # Создаем пользователя
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults={
                        'first_name': ' '.join(full_name.split()[1:]),
                        'last_name': full_name.split()[0],
                    }
                )
                
                if created:
                    user.set_password(user_data['password'])
                    user.save()
                    created_count += 1
                    status = self.style.SUCCESS('✓ СОЗДАН')
                else:
                    # Если пользователь уже существует, генерируем новый пароль
                    user.set_password(user_data['password'])
                    user.save()
                    skipped_count += 1
                    status = self.style.WARNING('⚠ УЖЕ СУЩЕСТВОВАЛ (пароль обновлен)')
                
                # Добавляем в проект как аннотатора
                member, member_created = Member.objects.get_or_create(
                    user=user,
                    project=project,
                    defaults={'role': annotator_role}
                )
                
                if not member_created:
                    # Обновляем роль если участник уже был в проекте
                    member.role = annotator_role
                    member.save()
                
                users_data.append(user_data)
                
                self.stdout.write(
                    f'{status} | {full_name:35} | {user_data["username"]:15} | {user_data["password"]}'
                )
                
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f'✗ ОШИБКА | {full_name:35} | Ошибка: {str(e)}')
                )
        
        # Создаем Excel файл
        self.stdout.write('\n' + '=' * 80)
        self.create_excel_report(users_data, output_file)
        
        # Итоговая статистика
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('ИТОГО:'))
        self.stdout.write(self.style.SUCCESS(f'  • Создано новых пользователей: {created_count}'))
        self.stdout.write(self.style.WARNING(f'  • Обновлено существующих: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'  • Всего обработано: {len(users_data)}'))
        self.stdout.write(self.style.SUCCESS(f'  • Все пользователи добавлены в проект: {project.name}'))
        self.stdout.write('=' * 80)
