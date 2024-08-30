import os
import requests
import zipfile
from tqdm import tqdm
from PyInquirer import prompt
from shutil import move, copytree, copy2

# Repositories to work with
REPOS = [
    {"name": "atmosphere", "url": "https://api.github.com/repos/Atmosphere-NX/Atmosphere/releases"},
    {"name": "hekate", "url": "https://api.github.com/repos/CTCaer/hekate/releases"},
    {"name": "sigpatches", "url": "https://sigmapatches.su/sigpatches.zip", "no_version": True}
]

# Define the paths
DOWNLOAD_PATH = './content/download/'
CONTENT_PATH = './content/'
TEST_PATH = './test/'
BACKUP_PATH = './backupdata/sdroot/'
BOOTLOADER_PAYLOADS_PATH = './test/bootloader/payloads/'

# Ensure the paths exist
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(CONTENT_PATH, exist_ok=True)
os.makedirs(TEST_PATH, exist_ok=True)
os.makedirs(BOOTLOADER_PAYLOADS_PATH, exist_ok=True)
os.makedirs(BACKUP_PATH, exist_ok=True)

# Get the list of releases from GitHub
def get_releases(repo_url):
    if repo_url.endswith(".zip"):
        return [{"tag_name": "latest", "assets": [{"browser_download_url": repo_url, "name": os.path.basename(repo_url)}]}]
    response = requests.get(repo_url)
    response.raise_for_status()
    return response.json()

# Display an interactive list of repositories to choose from
def choose_repositories():
    choices = [{'name': repo['name']} for repo in REPOS]
    choices.append({'name': 'Next'})  # Option to proceed to version selection
    questions = [
        {
            'type': 'checkbox',
            'name': 'repositories',
            'message': 'Select repositories to install:',
            'choices': choices,
            'pageSize': 10,
        }
    ]
    answers = prompt(questions)
    return [repo for repo in REPOS if repo['name'] in answers['repositories']]

# Display an interactive list of releases
def choose_release(releases, message='Select a version to download:'):
    if "no_version" in releases[0]:
        return releases[0]
    choices = [{'name': release['tag_name']} for release in releases]
    questions = [
        {
            'type': 'list',
            'name': 'release',
            'message': message,
            'choices': choices,
            'pageSize': 10,
        }
    ]
    answers = prompt(questions)
    return next(release for release in releases if release['tag_name'] == answers['release'])

# Download the selected release's ZIP file
def download_release(release, repo_name):
    asset = next((a for a in release['assets'] if a['name'].endswith('.zip')), None)

    if not asset:
        print(f"No suitable ZIP file found for {repo_name} in this release.")
        return

    zip_url = asset['browser_download_url']
    local_filename = os.path.join(DOWNLOAD_PATH, asset['name'])

    # Download with progress bar
    response = requests.get(zip_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    with open(local_filename, 'wb') as file, tqdm(
        desc=asset['name'],
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            file.write(data)
            bar.update(len(data))

    return local_filename

# Unzip the downloaded file
def unzip_file(zip_path, repo_name, release_tag):
    extract_to = os.path.join(CONTENT_PATH, repo_name, release_tag)
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Unzipped to: {extract_to}")

    # Backup "Nintendo" folder from ./test/ to ./backupdata/sdroot/
    nintendo_folder = os.path.join(TEST_PATH, 'Nintendo')
    if os.path.exists(nintendo_folder):
        move(nintendo_folder, BACKUP_PATH)
        print(f"'Nintendo' folder backed up to: {BACKUP_PATH}")

    # Copy contents to ./test/
    copytree(extract_to, TEST_PATH, dirs_exist_ok=True)
    print(f"Copied to: {TEST_PATH}")

    # If hekate, check for .bin file and move to ./bootloader/payloads/
    if repo_name == "hekate":
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                if file.startswith("hekate_ctcaer") and file.endswith(".bin"):
                    bin_path = os.path.join(root, file)
                    
                    # Delete existing hekate .bin files in test/ and bootloader/payloads/
                    for target_dir in [TEST_PATH, BOOTLOADER_PAYLOADS_PATH]:
                        for existing_file in os.listdir(target_dir):
                            if existing_file.startswith("hekate_ctcaer") and existing_file.endswith(".bin"):
                                os.remove(os.path.join(target_dir, existing_file))
                                print(f"Deleted existing {existing_file} from {target_dir}")

                    # Move new hekate .bin file to bootloader/payloads/
                    copy2(bin_path, BOOTLOADER_PAYLOADS_PATH)
                    print(f"Copied {file} to: {BOOTLOADER_PAYLOADS_PATH}")
                    break

# Main logic to handle the installation process
def main():
    # Step 1: Choose the installation method
    installation_options = ["Custom: Let me pick the latest versions of what is added"]
    
    questions = [
        {
            'type': 'list',
            'name': 'installation_method',
            'message': 'Choose how to install:',
            'choices': installation_options,
        }
    ]
    
    answers = prompt(questions)
    installation_method = answers['installation_method']
    
    if installation_method == "Custom: Let me pick the latest versions of what is added":
        # Step 2: Select repositories
        selected_repositories = choose_repositories()

        if not selected_repositories:
            print("No repositories selected.")
            return

        # Step 3: Select versions for each repository
        for repo in selected_repositories:
            releases = get_releases(repo['url'])
            selected_release = choose_release(releases, message=f"Select a version to download for {repo['name']}:")
            zip_file = download_release(selected_release, repo['name'])
            if zip_file:
                unzip_file(zip_file, repo['name'], selected_release['tag_name'])

if __name__ == '__main__':
    main()
