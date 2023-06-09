import os
import time
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def print_table(data, title):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for language, stats in data.items():
        table_data.append(
            [language, stats['Вакансий найдено'], stats['Вакансий обработано'], stats['Средняя зарплата']])
    table = AsciiTable(table_data, title)
    print(table.table)


def predict_hh_salary(salary):
    if not salary or salary['currency'] != 'RUR':
        return None
    if salary['from'] and salary['to']:
        return (salary['from'] + salary['to']) / 2
    elif salary['from']:
        return salary['from'] * 1.2
    elif salary['to']:
        return salary['to'] * 0.8


def predict_superjob_salary(payment_from, payment_to):
    if payment_from and payment_to:
        return (payment_from + payment_to) / 2
    elif payment_from:
        return payment_from * 1.2
    elif payment_to:
        return payment_to * 0.8


def get_hh_vacancies(language):
    vacancies_url = "https://api.hh.ru/vacancies"
    params = {
        'text': language,
        'area': '1',
        'per_page': '100',
    }
    all_vacancies = []
    page = 0
    while True:
        params['page'] = page
        response = requests.get(vacancies_url, params=params)
        response.raise_for_status()
        data = response.json()
        all_vacancies.extend(data['items'])
        if page >= data['pages'] - 1:
            break
        page += 1
        time.sleep(0.5)
    return all_vacancies, data['found']


def get_superjob_vacancies(language, api_key):
    vacancies_url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {'X-Api-App-Id': api_key}
    params = {
        'page': 0,
        'count': 100,
        'town': 'Москва',
        'keyword': language
    }

    all_vacancies = []

    page = 0
    while True:
        params['page'] = page
        response = requests.get(vacancies_url, headers=headers, params=params)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("Response content:", response.content)
            raise e

        data = response.json()
        all_vacancies.extend(data['objects'])
        if len(all_vacancies) >= data['total']:
            break
        page += 1
        time.sleep(0.5)
    return all_vacancies, data['total']


def fetch_sj_average_programmer_salaries(api_key, languages):
    vacancies_superjob_salaries = {}

    for language in languages:
        vacancies, total_vacancies = get_superjob_vacancies(language, api_key)
        salaries = []
        for vacancy in vacancies:
            predicted_salary = predict_superjob_salary(vacancy['payment_from'], vacancy['payment_to'])
            if predicted_salary:
                salaries.append(predicted_salary)
        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0
        vacancies_superjob_salaries[language] = {
            "Вакансий найдено": total_vacancies,
            "Вакансий обработано": len(salaries),
            "Средняя зарплата": average_salary
        }
        time.sleep(0.5)

    return vacancies_superjob_salaries


def fetch_hh_average_programmer_salaries(languages):
    vacancies_hh_salaries = {}

    for language in languages:
        vacancies, total_vacancies = get_hh_vacancies(language)
        salaries = []
        for vacancy in vacancies:
            predicted_salary = predict_hh_salary(vacancy['salary'])
            if predicted_salary:
                salaries.append(predicted_salary)
        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0
        vacancies_hh_salaries[language] = {
            "Вакансий найдено": total_vacancies,
            "Вакансий обработано": len(salaries),
            "Средняя зарплата": average_salary
        }
        time.sleep(0.5)

    return vacancies_hh_salaries


def main():
    load_dotenv()
    api_key = os.getenv('SUPER_JOB_KEY')
    languages = [
        'Python', 'Java', 'C++', 'JavaScript', 'C#', 'Swift', 'Kotlin', 'Ruby', 'PHP', 'Go'
    ]

    hh_average_programmer_salaries = fetch_hh_average_programmer_salaries(languages)
    print_table(hh_average_programmer_salaries, "HeadHunter Moscow")

    sj_average_programmer_salaries = fetch_sj_average_programmer_salaries(api_key, languages)
    print_table(sj_average_programmer_salaries, "SuperJob Moscow")


if __name__ == "__main__":
    main()