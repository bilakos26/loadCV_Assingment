import requests
from bs4 import BeautifulSoup as bs
import pathlib
import os
import logging
import json
import re
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from pydantic import BaseModel, ValidationError


FILE_PATH = pathlib.Path(__file__).resolve()
FOLDER_PATH = str(FILE_PATH.parent)

# delete's the previous scraper.log file so it can create a fresh one next
try:
    os.remove(FOLDER_PATH + '/scraper.log')
except Exception:
    pass

logging.basicConfig(filename=FOLDER_PATH + '/scraper.log', filemode='a', format='\n%(asctime)s - %(levelname)s - %(message)s')

url = "https://www.simplyhired.com/job/-VtS8-Ed22iC3MtJzfmU9tIxOwJNOZKi370vt3E7iWycUt0dg4Hdnw?isp=0&q=software+engineer"

# creating the information schema that we are going to gather from the webpage
class infoSchema(BaseModel):
    job_title: str
    company: str
    salary: list
    job_type: str
    qualifications: list
    description: str
    apply_link: str

# main scraper
class Scraper:
    
    def __init__(self):
        self.soup = ''
    
    # retrieve all the webpage info
    def retrieve_info(self):
        # execute get_response() function
        self.get_response() 
        
        try:
            job_title = self.soup.find('div', {'class':'viewjob-jobTitle h2'}).text.strip(" ").strip('\n')
            company = self.soup.find('div', {'class':'viewjob-labelWithIcon'}).text.split()
            company = " ".join(company[:-2]).strip(' ')
            location = self.soup.find_all('div', {'class':'viewjob-labelWithIcon'})[1].text.strip(' ')
            salary = self.soup.find('span', {'class':'viewjob-labelWithIcon viewjob-salary'}).text
            salary = re.findall('\$[\d,]+', salary)
            job_type = self.soup.find('span', {'class':'viewjob-labelWithIcon viewjob-jobType'}).text
            qualifications = self.soup.find_all('li', {'class':'viewjob-qualification'})
            qualifications = [i.text for i in qualifications]
            description = self.soup.find('div', {'data-testid':'VJ-section-content-jobDescription'}).text
            apply_link = self.soup.find('div', {'data-testid':'VJ-applyButton-container'}).find('a')['href']
            apply_link = "https://www.simplyhired.com" + apply_link
            
            try:
                infoItems = infoSchema(     # submiting the schema
                    job_title=job_title,
                    company=company,
                    location=location,
                    salary=salary,
                    job_type=job_type,
                    qualifications=qualifications, 
                    description=description,
                    apply_link=apply_link
                ).__dict__
                
                info = {url:infoItems}
                if url not in self.load_file(): # checks if the link already exists inside the .json file
                    self.save_file(info) # save's the info to the file
                else:
                    print("\nInfo from this webpage has been scrapped before.\n")
            except ValidationError:
                logging.error("VALIDATION ERROR", exc_info=True)
                print("\nValidation error!\n")
        except Exception:
            logging.error("RETRIEVE INFO ERROR", exc_info=True)
            print('\nRetrieve Info error!\n')
    
    # retrieve data from the website
    def get_response(self):
        try:
            response = requests.get(url, headers=self.userAgent()).text
            self.soup = bs(response, "html.parser")
        except Exception:
            logging.error("GET RESPONSE ERROR", exc_info=True)
            print('\nGet response error!\n')
        
    # retrieve a random user agent
    def userAgent(self):
        user_agent_rotator = UserAgent(
            software_names=SoftwareName.CHROME.value,
            operating_systems=[OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value],
            limit=100
        ).get_random_user_agent()
        
        header = {
            "user_agent":user_agent_rotator
        }
        
        return header
    
    # save json file
    def save_file(self, json_f):
        with open(FOLDER_PATH + '/extracted_info.json', 'w') as ex_info:
            json.dump(json_f, ex_info, indent=3)
            ex_info.close()
        
        print("\nInfo saved!\n")
        
    # load json info
    def load_file(self):
        try:
            with open(FOLDER_PATH + '/extracted_info.json', 'r') as ex_info:
                json_f = json.load(ex_info)
                ex_info.close()
            return json_f
        except Exception:
            return {}
            
    
if __name__ == "__main__":
    Scraper().retrieve_info()