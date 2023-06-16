import os
import time
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def print_table(json_vacancy_descriptions, title):
    table_columns = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for language, stats in json_vacancy_descriptions.items():
        table_columns.append(
            [language, stats['Вакансий найдено'], stats['Вакансий обработано'], stats['Средняя зарплата']])
    table = AsciiTable(table_columns, title)
    print(table.table)


def get_predicted_hh_salary(salary):
    if not salary or salary['currency'] != 'RUR':
        return None
    predicted_salary = predict_salary(salary['from'], salary['to'])
    return predicted_salary


def predict_salary(payment_from, payment_to):
    if payment_from and payment_to:
        return (payment_from + payment_to) / 2
    elif payment_from:
        return payment_from * 1.2
    elif payment_to:
        return payment_to * 0.8


def get_hh_vacancies(language):
    vacancies_url = "https://api.hh.ru/vacancies"
    area_id = '1'
    vacancies_per_page = '100'
    params = {
        'text': language,
        'area': area_id,
        'per_page': vacancies_per_page,
    }
    all_vacancies = []
    page = 0
    while True:
        params['page'] = page
        response = requests.get(vacancies_url, params=params)
        response.raise_for_status()
        json_vacancy_descriptions = response.json()
        all_vacancies.extend(json_vacancy_descriptions['items'])
        if page >= json_vacancy_descriptions['pages'] - 1:
            break
        page += 1
        time.sleep(0.5)
    return all_vacancies, json_vacancy_descriptions['found']


def get_superjob_vacancies(language, api_key):
    vacancies_url = "https://api.superjob.ru/2.0/vacancies/"
    start_page_number = 0
    vacancies_per_page = 100
    city_name = 'Москва'
    headers = {'X-Api-App-Id': api_key}
    params = {
        'page': start_page_number,
        'count': vacancies_per_page,
        'town': city_name,
        'keyword': language
    }

    all_vacancies = []

    page = 0
    while True:
        params['page'] = page
        response = requests.get(vacancies_url, headers=headers, params=params)

        json_vacancy_descriptions = response.json()
        all_vacancies.extend(json_vacancy_descriptions['objects'])
        if len(all_vacancies) >= json_vacancy_descriptions['total']:
            break
        page += 1
        time.sleep(0.5)
    return all_vacancies, json_vacancy_descriptions['total']


def fetch_sj_average_programmer_salaries(api_key, languages):
    vacancies_superjob_salaries = {}
    delay_time = 0.5

    for language in languages:
        vacancies, total_vacancies = get_superjob_vacancies(language, api_key)
        salaries = []
        for vacancy in vacancies:
            predicted_salary = predict_salary(vacancy['payment_from'], vacancy['payment_to'])
            if predicted_salary:
                salaries.append(predicted_salary)
        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0
        vacancies_superjob_salaries[language] = {
            "vacancies_found": total_vacancies,
            "vacancies_processed": len(salaries),
            "average_salary": average_salary
        }
        time.sleep(delay_time)

    return vacancies_superjob_salaries


def fetch_hh_average_programmer_salaries(languages):
    vacancies_hh_salaries = {}
    delay_time = 0.5

    for language in languages:
        vacancies, total_vacancies = get_hh_vacancies(language)
        salaries = []
        for vacancy in vacancies:
            predicted_salary = get_predicted_hh_salary(vacancy['salary'])
            if predicted_salary:
                salaries.append(predicted_salary)
        average_salary = int(sum(salaries) / len(salaries)) if salaries else 0
        vacancies_hh_salaries[language] = {
            "vacancies_found": total_vacancies,
            "vacancies_processed": len(salaries),
            "average_salary": average_salary
        }
        time.sleep(delay_time)

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