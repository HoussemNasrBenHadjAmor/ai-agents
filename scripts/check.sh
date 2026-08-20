uname -a

echo "---- OS ----"
cat /etc/os-release

echo "---- DOCKER ----"
docker --version

echo "---- COMPOSE ----"
docker compose version

echo "---- GIT ----"
git --version

echo "---- PYTHON ----"
python3 --version

echo "---- NODE ----"
node --version 2>/dev/null || echo "Node not installed"

echo "---- NPM ----"
npm --version 2>/dev/null || echo "npm not installed"

echo "---- DISK ----"
df -h /

echo "---- MEMORY ----"
free -h

echo "---- RUNNING CONTAINERS ----"
docker ps
